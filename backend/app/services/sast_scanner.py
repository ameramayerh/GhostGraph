import asyncio
import json
import os
import shutil
from typing import List
from ..models import Finding
from .logger import ws_manager

def extract_code_snippet(file_path: str, line_number: int, context_lines: int = 250) -> str:
    """Reads the source file and extracts a large window of lines around the finding."""
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
        return findings

    await ws_manager.broadcast("Running Software Composition Analysis (SCA) via npm audit...", "info")
    
    try:
        # We use --audit-level=moderate to filter out low severity noise
        process = await asyncio.create_subprocess_exec(
            "npm.cmd" if os.name == "nt" else "npm", "audit", "--json",
            cwd=target_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
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
                    desc = f"Vulnerable dependency detected: {pkg_name}\\n"
                    
                    if advisories and isinstance(advisories[0], dict):
                        adv = advisories[0]
                        cve = adv.get("title", "Vulnerable Dependency")
                        desc += f"\\nDetails: {adv.get('title', '')}"
                        desc += f"\\nUrl: {adv.get('url', '')}"
                    elif isinstance(advisories[0], str):
                        cve = f"Vulnerable module: {advisories[0]}"
                        
                    desc += f"\\nFix Available: {vuln_data.get('fixAvailable', False)}"
                    
                    finding = Finding(
                        engagement_id=engagement_id,
                        title=f"SCA: {pkg_name} ({cve})",
                        description=desc[:1000],
                        file_path="package.json",
                        line_number=1, # Defaulting to top of file
                        code_snippet=f"\"dependencies\": {{\n  ...\"{pkg_name}\": \"...\"\n}}",
                        semgrep_rule_id="npm-audit-cve",
                        severity=severity,
                        category="Software Composition Analysis"
                    )
                    findings.append(finding)
                    
                await ws_manager.broadcast(f"SCA completed. Found {len(findings)} vulnerable dependencies.", "success")
            except json.JSONDecodeError as e:
                await ws_manager.broadcast(f"Failed to parse npm audit output: {e}", "error")
    except Exception as e:
        await ws_manager.broadcast(f"npm audit encountered an exception: {str(e)}", "error")
        print(f"npm audit exception: {e}")
        
    return findings

async def run_semgrep_scan(engagement_id: int, target_dir: str) -> List[Finding]:
    """Runs Semgrep against the extracted source code directory."""
    findings = []
    
    await ws_manager.broadcast(f"Launching Semgrep SAST scan on {target_dir}...", "info")

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
        "--config", "p/default",
        "--config", "p/owasp-top-ten",
        "--config", "p/security-audit",
        "--config", "p/cwe-top-25",
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
        "--exclude", "*sample*",
        "--exclude", "*example*",
        "--exclude", "*mock*",
        "--exclude", "*docs*",
        "--exclude", "*tutorial*",
        "--exclude", "*demo*",
        "--exclude", "*lesson*",
        target_dir
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
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
                        file_path=file_path,
                        line_number=line_number,
                        code_snippet=extract_code_snippet(file_path, line_number) or extra.get("lines", ""),
                        semgrep_rule_id=result.get("check_id", "Unknown"),
                        severity=severity,
                        category="Static Analysis"
                    )
                    findings.append(finding)
                
                await ws_manager.broadcast(f"Semgrep scan completed. Found {len(findings)} issues.", "success")
            except json.JSONDecodeError as e:
                await ws_manager.broadcast(f"Failed to parse Semgrep output: {e}", "error")
        else:
             if stderr:
                 await ws_manager.broadcast(f"Semgrep error: {stderr.decode()}", "error")

    except Exception as e:
        await ws_manager.broadcast(f"Semgrep scan encountered an exception: {str(e)}", "error")
        print(f"Semgrep exception: {e}")
        
    return findings
