import os
import json
import asyncio
import logging
from typing import List
from ..models import Finding
from .logger import ws_manager
from .ai import GEMINI_PROVIDER, LOCAL_MODELS, ai_analyst, check_ollama_available
from sqlmodel import Session, select
from ..models import SystemSettings
from ..database import engine

logger = logging.getLogger(__name__)

async def run_ai_hunter(engagement_id: int, target_dir: str) -> List[Finding]:
    """
    Optionally reviews selected application files for authorization,
    authentication, and business-logic risks that rule-based scans may miss.
    """
    findings = []
    
    await ws_manager.broadcast("Checking whether optional AI review is available...", "info")
    
    # Prioritize files whose names commonly indicate security-sensitive workflows.
    interesting_keywords = [
        "auth", "login", "register", "user", "profile", "password", 
        "basket", "order", "payment", "coupon", "reward", "token", "jwt",
        "route", "controller", "api"
    ]
    
    target_files = []
    for root, dirs, files in os.walk(target_dir):
        # Exclude common noise directories
        dirs[:] = [d for d in dirs if d not in ['node_modules', 'dist', 'build', 'coverage', 'test', 'tests', 'vendor']]
        for file in files:
            if not file.endswith(('.js', '.ts')):
                continue
            
            file_lower = file.lower()
            if any(keyword in file_lower for keyword in interesting_keywords):
                target_files.append(os.path.join(root, file))
                
    # Bound the review to keep runtime and model context predictable.
    target_files = sorted(target_files)[:10]

    if not target_files:
        await ws_manager.broadcast("No security-sensitive files were selected for optional AI review.", "info")
        return findings

    await ws_manager.broadcast(f"Reviewing up to {len(target_files)} security-sensitive file(s) with AI...", "info")

    with Session(engine) as session:
        settings = session.exec(select(SystemSettings)).first()
        llm_provider = settings.llm_provider if settings else "local-llama3"
        api_key = settings.api_key if settings else None

    # AI is an optional enrichment feature. Do one availability check rather
    # than making every uploaded file wait for a failed model connection.
    if llm_provider == GEMINI_PROVIDER:
        if not api_key:
            await ws_manager.broadcast("AI review skipped: configure a Gemini API key to enable it.", "info")
            return findings
    else:
        model_name = LOCAL_MODELS.get(llm_provider)
        if not model_name:
            await ws_manager.broadcast("AI review skipped: unsupported provider configuration.", "error")
            return findings
        try:
            available, message = await asyncio.wait_for(
                asyncio.to_thread(check_ollama_available, model_name), timeout=3
            )
        except asyncio.TimeoutError:
            available, message = False, "Ollama availability check timed out."
        if not available:
            await ws_manager.broadcast(f"AI review skipped: {message}", "info")
            return findings

    prompt_template = """
You are an application-security reviewer.
Review the following source file for risks that rule-based static analysis may miss.
Specifically look for:
1. Insecure Direct Object References (IDOR) - Using user-supplied IDs to fetch database records without checking if the current user owns that record.
2. Business Logic Flaws - Coupon abuse, manipulating quantities to be negative, bypassing workflow steps.
3. Authentication / Authorization - Weak JWT secrets, lack of middleware protecting sensitive routes, bypassable password resets.

Respond ONLY with a valid JSON array of vulnerability objects. 
If no vulnerabilities are found, respond with [].
Do not include markdown blocks like ```json. Just raw JSON.

Format:
[
  {
    "title": "Short vulnerability name",
    "description": "Detailed explanation of the flaw and impact",
    "line_number": 10,
    "severity": "High",
    "semgrep_rule_id": "ai-threat-hunter-logic-flaw"
  }
]

File: {file_name}
Code:
{code}
"""

    total_hunts = 0
    
    for file_path in target_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # Skip files larger than the configured review context.
            if len(code) > 50000:
                continue
                
            relative_path = os.path.relpath(file_path, target_dir)
            prompt = prompt_template.replace("{file_name}", relative_path).replace("{code}", code)
            
            response = await asyncio.to_thread(
                ai_analyst.generate, prompt, llm_provider, api_key
            )
            
            # Parse the JSON response
            # Sometimes LLMs wrap in markdown anyway, so clean it
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.startswith("```"):
                clean_response = clean_response[3:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            
            clean_response = clean_response.strip()
            
            if clean_response and clean_response != "[]":
                try:
                    vulns = json.loads(clean_response)
                    if isinstance(vulns, list):
                        for vuln in vulns:
                            try:
                                line_num = max(1, int(vuln.get("line_number", 1)))
                            except (TypeError, ValueError):
                                line_num = 1
                            lines = code.splitlines()
                            start = max(0, line_num - 5)
                            end = min(len(lines), line_num + 5)
                            snippet = "\n".join(lines[start:end])

                            severity = str(vuln.get("severity", "High")).title()
                            if severity not in {"Critical", "High", "Medium", "Low"}:
                                severity = "High"
                            
                            finding = Finding(
                                engagement_id=engagement_id,
                                title=f"AI Review: {vuln.get('title', 'Potential logic flaw')}",
                                description=str(vuln.get('description', 'Identified during optional LLM-assisted review.'))[:1000],
                                file_path=relative_path,
                                line_number=line_num,
                                code_snippet=snippet,
                                semgrep_rule_id=vuln.get("semgrep_rule_id", "ai-logic-flaw"),
                                severity=severity,
                                category="AI-Assisted Review"
                            )
                            findings.append(finding)
                            total_hunts += 1
                except json.JSONDecodeError:
                    logger.warning("Invalid AI review JSON for %s", relative_path)
                    
            # Briefly yield between requests without adding a long artificial delay.
            await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.exception("AI review failed for %s", file_path)
            
    await ws_manager.broadcast(f"Optional AI review complete. Reported {total_hunts} potential issues.", "success")
    return findings
