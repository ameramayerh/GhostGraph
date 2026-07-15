import os
import glob
import json
import asyncio
from typing import List
from ..models import Finding
from .logger import ws_manager
from .ai import ai_analyst, check_ollama_available
from sqlmodel import Session, select
from ..models import SystemSettings
from ..database import engine

async def run_ai_hunter(engagement_id: int, target_dir: str) -> List[Finding]:
    """
    Uses the local LLM as an Agentic Threat Hunter to find Business Logic, 
    IDOR, and Authentication flaws in specific, high-value files.
    """
    findings = []
    
    await ws_manager.broadcast("Initializing Agentic Threat Hunter for deep logic analysis...", "info")
    
    # Identify high-value files based on Juice Shop / Express typical patterns
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
                
    # To prevent completely blowing up the local LLM, we limit to the top 20 most likely files
    # or just sort them and take a chunk. For a real pentest, we'd do all of them.
    target_files = sorted(target_files)[:20] 

    if not target_files:
        await ws_manager.broadcast("No high-value files identified for AI Hunting.", "info")
        return findings

    await ws_manager.broadcast(f"AI Hunter identified {len(target_files)} high-value files. Commencing deep analysis...", "info")

    with Session(engine) as session:
        settings = session.exec(select(SystemSettings)).first()
        llm_provider = settings.llm_provider if settings else "local-llama3"
        api_key = settings.api_key if settings else None

    # AI is an optional enrichment feature. Do one availability check rather
    # than making every uploaded file wait for a failed model connection.
    if "gemini" in llm_provider.lower():
        if not api_key:
            await ws_manager.broadcast("AI Hunter skipped: configure a Gemini API key to enable it.", "info")
            return findings
    else:
        model_name = "mistral" if "mistral" in llm_provider.lower() else "llama3"
        try:
            available, message = await asyncio.wait_for(
                asyncio.to_thread(check_ollama_available, model_name), timeout=3
            )
        except asyncio.TimeoutError:
            available, message = False, "Ollama availability check timed out."
        if not available:
            await ws_manager.broadcast(f"AI Hunter skipped: {message}", "info")
            return findings

    prompt_template = """
You are an expert Application Security Penetration Tester.
Review the following source code file for advanced vulnerabilities that static analysis misses.
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
                
            # Skip massive files (e.g. over 1000 lines or 50KB) to save context window
            if len(code) > 50000:
                continue
                
            relative_path = os.path.relpath(file_path, target_dir)
            prompt = prompt_template.replace("{file_name}", relative_path).replace("{code}", code)
            
            # Send to LLM
            await ws_manager.broadcast(f"AI Hunter analyzing: {relative_path}...", "info")
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
                            # Try to extract a snippet around the reported line
                            try:
                                line_num = max(1, int(vuln.get("line_number", 1)))
                            except (TypeError, ValueError):
                                line_num = 1
                            lines = code.split('\\n')
                            start = max(0, line_num - 5)
                            end = min(len(lines), line_num + 5)
                            snippet = "\\n".join(lines[start:end])
                            
                            finding = Finding(
                                engagement_id=engagement_id,
                                title=f"AI Hunter: {vuln.get('title', 'Business Logic Flaw')}",
                                description=vuln.get('description', 'Identified by AI Agentic Threat Hunter.')[:1000],
                                file_path=relative_path,
                                line_number=line_num,
                                code_snippet=snippet,
                                semgrep_rule_id=vuln.get("semgrep_rule_id", "ai-logic-flaw"),
                                severity=vuln.get("severity", "High"),
                                category="AI Deep Analysis"
                            )
                            findings.append(finding)
                            total_hunts += 1
                except json.JSONDecodeError:
                    print(f"Failed to decode AI Hunter JSON for {relative_path}: {clean_response}")
                    
            # Brief sleep to avoid rate limiting / melting the local machine
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Error in AI Hunter for {file_path}: {e}")
            
    await ws_manager.broadcast(f"Agentic Threat Hunting complete. Discovered {total_hunts} deep logic flaws.", "success")
    return findings
