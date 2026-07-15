from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from sqlmodel import Session, select, func, delete
from typing import List
import asyncio
import os
import tempfile
import zipfile
import shutil
import traceback
from pathlib import Path
from datetime import datetime

from .models import Engagement, AuditLog, Finding, SystemSettings
from .database import get_session
from .services.sast_scanner import run_semgrep_scan, run_npm_audit
from .services.ai_hunter import run_ai_hunter
from .services.ai import ai_analyst
from .services.logger import ws_manager
from .services.report_generator import generate_pdf_report
from fastapi.responses import StreamingResponse

router = APIRouter()
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
MAX_EXTRACTED_BYTES = 500 * 1024 * 1024


async def save_upload(file: UploadFile, destination: str) -> None:
    """Persist an upload with a bounded size so scans cannot exhaust disk space."""
    written = 0
    with open(destination, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="ZIP files must be 100 MB or smaller.")
            buffer.write(chunk)


def extract_zip_safely(zip_path: str, destination: str) -> None:
    """Reject path-traversal and oversized archives before extracting them."""
    destination_path = Path(destination).resolve()
    with zipfile.ZipFile(zip_path, "r") as archive:
        if sum(entry.file_size for entry in archive.infolist()) > MAX_EXTRACTED_BYTES:
            raise HTTPException(status_code=413, detail="ZIP contents are too large to scan.")
        for entry in archive.infolist():
            target = (destination_path / entry.filename).resolve()
            if not target.is_relative_to(destination_path):
                raise HTTPException(status_code=400, detail="ZIP contains an unsafe file path.")
        archive.extractall(destination_path)

@router.post("/engagements", response_model=Engagement)
def create_engagement(engagement: Engagement, session: Session = Depends(get_session)):
    if not engagement.authorized_by:
        raise HTTPException(status_code=400, detail="Authorization confirmation is required to start an engagement.")
    
    session.add(engagement)
    session.commit()
    session.refresh(engagement)
    
    audit_log = AuditLog(
        engagement_id=engagement.id,
        action="Engagement Created",
        user=engagement.authorized_by,
        details=f"Project scope defined: {engagement.scope}"
    )
    session.add(audit_log)
    session.commit()
    
    return engagement

@router.get("/engagements", response_model=List[Engagement])
def read_engagements(session: Session = Depends(get_session)):
    engagements = session.exec(select(Engagement)).all()
    return engagements

@router.get("/engagements/{engagement_id}/audit", response_model=List[AuditLog])
def read_engagement_audit_logs(engagement_id: int, session: Session = Depends(get_session)):
    logs = session.exec(select(AuditLog).where(AuditLog.engagement_id == engagement_id)).all()
    return logs

@router.post("/engagements/{engagement_id}/scan")
async def upload_and_scan(
    engagement_id: int, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    session: Session = Depends(get_session)
):
    engagement = session.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are supported.")

    audit_log = AuditLog(
        engagement_id=engagement.id,
        action="ZIP Upload Initiated",
        user=engagement.authorized_by,
        details=f"Uploaded source code: {file.filename}"
    )
    session.add(audit_log)
    session.commit()
    
    await ws_manager.broadcast(f"Extracting source code from {file.filename}...", "info")
    
    # Extract to a temp directory
    temp_dir = tempfile.mkdtemp(prefix="sentinel_")
    zip_path = os.path.join(temp_dir, "upload.zip")
    
    try:
        await save_upload(file, zip_path)
            
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        
        extract_zip_safely(zip_path, extract_dir)
            
        await ws_manager.broadcast(f"Extraction complete. Starting SAST scan...", "info")
        
        # Run SCA (npm audit)
        sca_findings = await run_npm_audit(engagement.id, extract_dir)
        
        # Run SAST (Semgrep)
        sast_findings = await run_semgrep_scan(engagement.id, extract_dir)
        
        # Run Agentic Threat Hunter (LLM)
        ai_findings = await run_ai_hunter(engagement.id, extract_dir)
        
        findings = sca_findings + sast_findings + ai_findings
        
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e) or repr(e)
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Scan failed: {error_msg}")
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    # Clear previous
    session.exec(delete(Finding).where(Finding.engagement_id == engagement_id))
    session.commit()
    
    # Smart De-Duplication
    deduped_findings = []
    
    # Sort by file path, then title, then line number
    findings.sort(key=lambda x: (x.file_path, x.title, x.line_number))
    
    for finding in findings:
        if not deduped_findings:
            deduped_findings.append(finding)
            continue
            
        last = deduped_findings[-1]
        
        # If same file, same vulnerability title, and within 5 lines, group them
        if last.file_path == finding.file_path and last.title == finding.title:
            if abs(last.line_number - finding.line_number) <= 5:
                # Merge them: keep the earlier line number, combine snippets if different
                last.line_number = min(last.line_number, finding.line_number)
                if finding.code_snippet and finding.code_snippet not in last.code_snippet:
                    last.code_snippet += f"\\n...\\n{finding.code_snippet}"
                continue
                
        deduped_findings.append(finding)
        
    # Store new
    for finding in deduped_findings:
        session.add(finding)
        
    engagement.total_findings = len(deduped_findings)
    engagement.filtered_findings = 0
    session.add(engagement)
    session.commit()
    
    audit_log_complete = AuditLog(
        engagement_id=engagement.id,
        action="SAST Scan Completed",
        user="GhostGraph Engine",
        details=f"Identified {len(deduped_findings)} findings (de-duplicated from {len(findings)}). AI Pre-Filtering started."
    )
    session.add(audit_log_complete)
    session.commit()
    
    # Trigger background AI Noise Reduction
    background_tasks.add_task(background_noise_reduction, engagement.id)
    
    return {"status": "success", "findings_count": len(deduped_findings)}

async def background_noise_reduction(engagement_id: int):
    from sqlmodel import Session
    from .database import engine
    
    await ws_manager.broadcast("AI Pre-Filtering Pipeline started in background...", "info")
    
    with Session(engine) as session:
        settings = session.exec(select(SystemSettings)).first()
        llm_provider = settings.llm_provider if settings else "local-llama3"
        api_key = settings.api_key if settings else None
        
        findings = session.exec(select(Finding).where(Finding.engagement_id == engagement_id)).all()
        
        false_positives = 0
        for finding in findings:
            finding.filtering_status = "In Progress"
            session.add(finding)
            session.commit()
            
            try:
                evidence = f"File: {finding.file_path}:{finding.line_number}\\n{finding.code_snippet}"
                result = await asyncio.to_thread(
                    ai_analyst.evaluate_false_positive, finding.title, finding.description, evidence, llm_provider, api_key
                )
                
                finding.is_false_positive = result.get("is_false_positive", False)
                if finding.is_false_positive:
                    false_positives += 1
                finding.filtering_status = "Reviewed"
                session.add(finding)
                
                # Update progress
                engagement = session.get(Engagement, engagement_id)
                if engagement:
                    engagement.filtered_findings += 1
                    session.add(engagement)
                    
                session.commit()
                
                # Sleep briefly to avoid hammering the LLM locally
                await asyncio.sleep(0.5)
            except Exception as e:
                finding.filtering_status = "Error"
                session.add(finding)
                
                # Update progress even on error so progress bar finishes
                engagement = session.get(Engagement, engagement_id)
                if engagement:
                    engagement.filtered_findings += 1
                    session.add(engagement)
                    
                session.commit()
                
        # Log completion
        audit = AuditLog(
            engagement_id=engagement_id,
            action="AI Pre-Filtering Completed",
            user="GhostGraph AI Evaluator",
            details=f"Filtered {len(findings)} findings. Identified {false_positives} false positives."
        )
        session.add(audit)
        session.commit()
        
        await ws_manager.broadcast(f"AI Pre-Filtering Complete. Removed {false_positives} false positives.", "success")

@router.get("/engagements/{engagement_id}/findings", response_model=List[Finding])
def read_engagement_findings(engagement_id: int, session: Session = Depends(get_session)):
    findings = session.exec(select(Finding).where(Finding.engagement_id == engagement_id)).all()
    return findings

@router.post("/findings/{finding_id}/analyze")
async def analyze_finding(finding_id: int):
    from sqlmodel import Session
    from .database import engine
    
    with Session(engine) as session:
        finding = session.get(Finding, finding_id)
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        
        if finding.ai_explanation:
            return finding
            
        title = finding.title
        desc = finding.description
        code_snippet = finding.code_snippet
        file_path = finding.file_path
        line_num = str(finding.line_number)
        engagement_id = finding.engagement_id

        settings = session.exec(select(SystemSettings)).first()
        llm_provider = settings.llm_provider if settings else "local-llama3"
        api_key = settings.api_key if settings else None

    # We send the code snippet and file context instead of HTTP evidence
    evidence_text = f"File: {file_path}:{line_num}\nCode:\n{code_snippet}"
    
    try:
        analysis = await asyncio.to_thread(
            ai_analyst.analyze_finding, title, desc, evidence_text, llm_provider, api_key
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e) or repr(e)}")
    
    with Session(engine) as session:
        finding = session.get(Finding, finding_id)
        
        finding.ai_explanation = analysis.get("explanation", "No explanation provided.")
        finding.business_impact = analysis.get("business_impact", "Unknown")
        finding.remediation = analysis.get("remediation", "No remediation provided.")
        finding.confidence_level = analysis.get("confidence", "Unknown")
        
        # Optionally support code patch if the agent generates it
        finding.code_patch = analysis.get("code_patch", None)
        
        session.add(finding)
        
        audit_log = AuditLog(
            engagement_id=engagement_id,
            action="AI Educational Analysis",
            user="GhostGraph AI Pair Programmer",
            details=f"Analyzed finding: {title}"
        )
        session.add(audit_log)
        session.commit()
        session.refresh(finding)
        
        return finding

@router.get("/engagements/{engagement_id}/details")
def get_engagement_details(engagement_id: int, session: Session = Depends(get_session)):
    engagement = session.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    findings = session.exec(select(Finding).where(Finding.engagement_id == engagement_id)).all()
    audit_logs = session.exec(select(AuditLog).where(AuditLog.engagement_id == engagement_id).order_by(AuditLog.timestamp.desc())).all()
    
    return {
        "engagement": engagement,
        "findings": findings,
        "audit_logs": audit_logs
    }

@router.get("/engagements/{engagement_id}/report/pdf")
def get_engagement_pdf_report(engagement_id: int, session: Session = Depends(get_session)):
    engagement = session.get(Engagement, engagement_id)
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")
    
    findings = session.exec(select(Finding).where(Finding.engagement_id == engagement_id)).all()
    audit_logs = session.exec(select(AuditLog).where(AuditLog.engagement_id == engagement_id).order_by(AuditLog.timestamp.desc())).all()
    
    pdf_buffer = generate_pdf_report(engagement, findings, audit_logs)
    
    # Return as a downloadable file
    headers = {
        'Content-Disposition': f'attachment; filename="GhostGraph_AI_Report_{engagement.name.replace(" ", "_")}.pdf"'
    }
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)

@router.get("/analytics")
def get_analytics(session: Session = Depends(get_session)):
    total_assets = session.exec(select(func.count(Engagement.id))).one()
    active_engagements = session.exec(select(func.count(Engagement.id)).where(Engagement.status == "Active")).one()
    
    severity_counts = session.exec(
        select(Finding.severity, func.count(Finding.id)).group_by(Finding.severity)
    ).all()
    
    category_counts = session.exec(
        select(Finding.category, func.count(Finding.id)).group_by(Finding.category)
    ).all()
    
    critical_risks = sum(count for sev, count in severity_counts if sev in {"High", "Critical"})
    
    return {
        "totalAssets": total_assets,
        "activeEngagements": active_engagements,
        "criticalRisks": critical_risks,
        "severityData": [{"name": sev, "value": count, "color": "#ef4444" if sev in ["High", "Critical"] else "#eab308" if sev == "Medium" else "#3b82f6"} for sev, count in severity_counts],
        "categoryData": [{"name": cat, "count": count} for cat, count in category_counts]
    }

@router.get("/threat-intel")
def get_threat_intel():
    from .services.threat_intel import threat_intel_db
    try:
        # Get up to 100 entries from the collection
        result = threat_intel_db.collection.get(limit=100)
        
        intel_data = []
        if result and result.get("ids"):
            for i in range(len(result["ids"])):
                doc_id = result["ids"][i]
                doc_text = result["documents"][i] if result.get("documents") else ""
                metadata = result["metadatas"][i] if result.get("metadatas") and result["metadatas"][i] else {}
                
                intel_data.append({
                    "id": doc_id,
                    "source": metadata.get("source", "Local Vector DB"),
                    "type": metadata.get("type", "Intel Concept"),
                    "description": doc_text
                })
        return intel_data
    except Exception as e:
        print(f"Error fetching threat intel: {e}")
        return []

@router.get("/settings")
def get_settings(session: Session = Depends(get_session)):
    settings = session.exec(select(SystemSettings)).first()
    if not settings:
        settings = SystemSettings()
        session.add(settings)
        session.commit()
        session.refresh(settings)
    return {
        "id": settings.id,
        "llm_provider": settings.llm_provider,
        "has_api_key": bool(settings.api_key),
        "updated_at": settings.updated_at,
    }

@router.post("/settings")
def update_settings(new_settings: SystemSettings, session: Session = Depends(get_session)):
    settings = session.exec(select(SystemSettings)).first()
    if not settings:
        settings = SystemSettings()
        session.add(settings)
        
    settings.llm_provider = new_settings.llm_provider
    if new_settings.api_key:
        settings.api_key = new_settings.api_key
    settings.updated_at = datetime.utcnow()
        
    session.add(settings)
    session.commit()
    session.refresh(settings)
    return {
        "status": "success",
        "settings": {
            "id": settings.id,
            "llm_provider": settings.llm_provider,
            "has_api_key": bool(settings.api_key),
            "updated_at": settings.updated_at,
        },
    }

@router.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
