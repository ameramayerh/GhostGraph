import asyncio
import json
import logging
import os
import shutil
from typing import List
from ..models import Finding
from .logger import ws_manager

logger = logging.getLogger(__name__)

def extract_code_snippet(file_path: str, line_number: int, context_lines: int = 4) -> str:
    """Read a bounded source-code window around a finding."""
    if not os.path.exists(file_path) or line_number <= 0:
        return ""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        start_idx = max(0, line_number - 1 - context_lines)
        end_idx = min(len(lines), line_number + context_lines)
        
        snippet = ""
        for i in range(start_idx, end_idx):
            prefix = ">> " if i == line_number - 1 else "   "
            snippet += f"{i + 1:4d} | {prefix}{lines[i]}"
            
        return snippet.strip()
    except Exception:
        return ""

async def run_npm_audit(engagement_id: int, target_dir: str) -> List[Finding]:
    """Runs Software Composition Analysis (SCA) using npm audit to detect vulnerable dependencies and CVEs."""
    findings = []
    package_json_path = os.path.join(target_dir, "package.json")
    if not os.path.exists(package_json_path):
        for root, dirs, files in os.walk(target_dir):
            dirs[:] = [directory for directory in dirs if directory not in {"node_modules", ".git"}]
            if "package.json" in files:
                package_json_path = os.path.join(root, "package.json")
                break

    if not os.path.exists(package_json_path):
        return findings

    await ws_manager.broadcast("Checking third-party packages for known vulnerabilities...", "info")
    
    try:
        # We use --audit-level=moderate to filter out low severity noise
        process = await asyncio.create_subprocess_exec(
            "npm.cmd" if os.name == "nt" else "npm", "audit", "--json",
            cwd=os.path.dirname(package_json_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            await ws_manager.broadcast("Dependency check timed out; continuing with source-code checks.", "warning")
            return findings
        
        # npm audit exits with non-zero code if vulnerabilities are found, so we don't check returncode
        if stdout:
            try:
                data = json.loads(stdout.decode('utf-8'))
                vulnerabilities = data.get("vulnerabilities", {})
                
                for pkg_name, vuln_data in vulnerabilities.items():
                    # Extract the highest severity issue for this package
                    severity_raw = vuln_data.get("severity", "moderate").upper()
                    if severity_raw in ["CRITICAL", "HIGH"]:
                        severity = "Critical" if severity_raw == "CRITICAL" else "High"
                    else:
                        severity = "Medium"
                        
                    advisories = vuln_data.get("via", [])
                    cve = "Unknown CVE"
                    desc = f"Vulnerable dependency detected: {pkg_name}\n"
                    
                    if advisories and isinstance(advisories[0], dict):
                        adv = advisories[0]
                        cve = adv.get("title", "Vulnerable Dependency")
                        desc += f"\nDetails: {adv.get('title', '')}"
                        desc += f"\nURL: {adv.get('url', '')}"
                    elif advisories and isinstance(advisories[0], str):
                        cve = f"Vulnerable module: {advisories[0]}"
                        
                    desc += f"\nFix available: {vuln_data.get('fixAvailable', False)}"
                    
                    finding = Finding(
                        engagement_id=engagement_id,
                        title=f"SCA: {pkg_name} ({cve})",
                        description=desc[:1000],
                        file_path=os.path.relpath(package_json_path, target_dir),
                        line_number=1, # Defaulting to top of file
                        code_snippet=f"\"dependencies\": {{\n  ...\"{pkg_name}\": \"...\"\n}}",
                        semgrep_rule_id="npm-audit-cve",
                        severity=severity,
                        category="Software Composition Analysis"
                    )
                    findings.append(finding)
                    
                await ws_manager.broadcast(f"Dependency check complete: {len(findings)} issue(s) found.", "success")
            except json.JSONDecodeError as e:
                await ws_manager.broadcast("Dependency check returned unreadable results.", "error")
                logger.warning("Failed to parse npm audit output: %s", e)
    except Exception as e:
        await ws_manager.broadcast("Dependency check could not complete.", "error")
        logger.exception("npm audit failed")
        
    return findings

async def run_semgrep_scan(engagement_id: int, target_dir: str) -> List[Finding]:
    """Runs Semgrep against the extracted source code directory."""
    findings = []
    
    await ws_manager.broadcast("Checking source code for unsafe patterns...", "info")

    import sys
    # Try to find semgrep in the current virtualenv Scripts directory first (for Windows)
    venv_semgrep = os.path.join(sys.prefix, "Scripts", "semgrep.exe")
    if os.path.exists(venv_semgrep):
        semgrep_path = venv_semgrep
    else:
        semgrep_path = shutil.which("semgrep") or "semgrep"
    
    cmd = [
        semgrep_path, "scan",
        "--json",
        "--config", os.path.join(os.path.dirname(__file__), "rules", "ghostgraph.yml"),
        "--exclude", "*test*",
        "--exclude", "*spec*",
        "--exclude", "node_modules",
        "--exclude", "vendor",
        "--exclude", "dist",
        "--exclude", "build",
        "--exclude", "coverage",
        "--exclude", ".github",
        "--exclude", ".gitlab",
        "--exclude", "Jenkinsfile",
        target_dir
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        except asyncio.TimeoutError:
            process.kill()
            await process.communicate()
            await ws_manager.broadcast("Source-code check timed out; continuing with available results.", "warning")
            return findings
        
        if stdout:
            try:
                data = json.loads(stdout.decode())
                results = data.get("results", [])
                
                for result in results:
                    extra = result.get("extra", {})
                    severity_raw = extra.get("severity", "WARNING")
                    
                    title = result.get("check_id", "Semgrep Finding").split(".")[-1].replace("-", " ").title()
                    
                    # Map Semgrep severity to our model
                    if severity_raw == "ERROR":
                        critical_keywords = ["injection", "sql", "rce", "xxe", "exec", "command", "eval"]
                        if any(k in title.lower() for k in critical_keywords):
                            severity = "Critical"
                        else:
                            severity = "High"
                    elif severity_raw == "WARNING":
                        severity = "Medium"
                    else:
                        severity = "Low"

                    file_path = result.get("path", "Unknown")
                    line_number = result.get("start", {}).get("line", 0)
                    
                    finding = Finding(
                        engagement_id=engagement_id,
                        title=title,
                        description=extra.get("message", "No description provided.")[:1000],
                        file_path=os.path.relpath(file_path, target_dir) if os.path.isabs(file_path) else file_path,
                        line_number=line_number,
                        code_snippet=extract_code_snippet(file_path, line_number) or extra.get("lines", ""),
                        semgrep_rule_id=result.get("check_id", "Unknown"),
                        severity=severity,
                        category="Static Analysis"
                    )
                    findings.append(finding)
                
                await ws_manager.broadcast(f"Source-code check complete: {len(findings)} issue(s) found.", "success")
            except json.JSONDecodeError as e:
                await ws_manager.broadcast("Source-code check returned unreadable results.", "error")
                logger.warning("Failed to parse Semgrep output: %s", e)
        else:
             if stderr:
                 await ws_manager.broadcast("Source-code check could not complete.", "error")
                 logger.error("Semgrep error: %s", stderr.decode(errors="replace"))

    except Exception as e:
        await ws_manager.broadcast("Source-code check could not complete.", "error")
        logger.exception("Semgrep scan failed")
        
    return findings
