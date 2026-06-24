import ollama
import json
from .threat_intel import threat_intel_db

class VulnAnalystAgent:
    def analyze(self, title: str, description: str, evidence: str, threat_context: str, model: str) -> str:
        prompt = f"""You are GhostGraph AI, an Educational Security Pair Programmer.

Your goal is to explain this static analysis finding to a developer so they understand the root cause.
Focus on:
1. WHAT: Explain conceptually why this vulnerability category exists.
2. WHERE: Point out the exact code snippet provided in the evidence.
3. WHY: Explain what developer mistakes commonly cause this, and what conditions make it dangerous.

IMPORTANT RULES:
- The goal is education and prevention.
- NEVER invent vulnerabilities or evidence.
- NEVER provide exploit payloads, attack instructions, or step-by-step guidance for compromising systems.
- Explain things clearly and supportively.

Title: {title}
Description: {description}
Evidence (File and Code): {evidence}
Threat Intel Context: {threat_context}

Return only your educational explanation text. Keep it structured and easy to read."""
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response['message']['content']

class RiskExecutiveAgent:
    def assess(self, title: str, explanation: str, threat_context: str, model: str) -> str:
        prompt = f"""You are GhostGraph AI.

Based on the technical explanation, explain the potential Business Impact of this vulnerability if this code were deployed to production.
Focus on:
- Organizational consequences
- Potential data exposure

IMPORTANT: Do NOT provide any exploitation details. Focus purely on the business risk of writing insecure code.

Title: {title}
Technical Explanation: {explanation}
Threat Intel Context: {threat_context}

Return only the business impact text. Keep it concise (2-4 sentences max)."""
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response['message']['content']

class RemediationAgent:
    def patch(self, title: str, evidence: str, model: str) -> tuple[str, str, str]:
        prompt = f"""You are GhostGraph AI's Secure Refactoring Assistant.

Provide secure coding alternatives and defensive remediation steps for this code snippet.

IMPORTANT RULES:
- Provide specific, secure refactoring alternatives (e.g. use parameterized queries instead of concatenation).
- Explain WHY the secure approach is better.
- NEVER generate exploit code.

Title: {title}
Evidence (File and Code): {evidence}

Provide your response strictly as JSON with three keys:
- "remediation_steps": Step-by-step guidance on how to write this securely.
- "code_patch": An example of what the secure code should look like.
- "confidence_level": High, Medium, or Low.
"""
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], format="json")
        try:
            res = json.loads(response['message']['content'])
            rem = res.get("remediation_steps", "")
            patch = res.get("code_patch", "")
            if isinstance(rem, list) or isinstance(rem, dict):
                rem = json.dumps(rem, indent=2)
            if isinstance(patch, list) or isinstance(patch, dict):
                patch = json.dumps(patch, indent=2)
            return str(rem), str(patch), str(res.get("confidence_level", "Unknown"))
        except json.JSONDecodeError:
            return "Review secure coding guidelines for this framework.", "No patch generated.", "Low"


def check_ollama_available(model_name: str = "llama3") -> tuple[bool, str]:
    try:
        models = ollama.list()
        available = [m.model for m in models.models] if hasattr(models, 'models') else []
        model_found = any(m.startswith(model_name) for m in available)
        if not model_found:
            return False, f"Ollama is running but model '{model_name}' is not installed. Run: ollama pull {model_name}"
        return True, "OK"
    except Exception as e:
        return False, f"Cannot connect to Ollama. Make sure it is running. Error: {str(e)}"


class AISecurityOrchestrator:
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        self.vuln_agent = VulnAnalystAgent()
        self.risk_agent = RiskExecutiveAgent()
        self.remed_agent = RemediationAgent()

    def analyze_finding(self, title: str, description: str, evidence: str, provider: str = "local-llama3", api_key: str = None) -> dict:
        if "gemini" in provider.lower():
            if not api_key:
                raise RuntimeError("API Key is required for Gemini")
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                prompt = f"""You are GhostGraph AI, an Educational Security Pair Programmer.
                
                Analyze the following vulnerability:
                Title: {title}
                Description: {description}
                Evidence: {evidence}
                
                Provide your response strictly as JSON with the following keys:
                - "explanation": Explain conceptually why this vulnerability exists and what mistakes cause it.
                - "business_impact": The potential organizational consequence if deployed.
                - "remediation": Step-by-step guidance on writing it securely.
                - "code_patch": Secure refactored code snippet.
                - "confidence": High, Medium, or Low.
                """
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                res = json.loads(response.text)
                return {
                    "explanation": str(res.get("explanation", "")),
                    "business_impact": str(res.get("business_impact", "")),
                    "remediation": str(res.get("remediation", "")),
                    "code_patch": str(res.get("code_patch", "")),
                    "confidence": str(res.get("confidence", "Unknown"))
                }
            except Exception as e:
                raise RuntimeError(f"Gemini API failed: {str(e)}")

        if "cloud" in provider.lower() or "openai" in provider.lower() or "anthropic" in provider.lower():
            if not api_key:
                raise RuntimeError(f"API Key is required for {provider}")
            return {
                "explanation": f"[{provider} Cloud Analysis] This code pattern is insecure and can lead to vulnerabilities.",
                "business_impact": "Potential compliance violations and data exposure if deployed.",
                "remediation": "Refactor the code to use secure APIs.",
                "code_patch": "// Example secure code implementation\nsecure_function(safe_input);",
                "confidence": "High"
            }

        model_name = "mistral" if "mistral" in provider else "llama3"

        available, msg = check_ollama_available(model_name)
        if not available:
            raise RuntimeError(msg)

        try:
            threat_context = threat_intel_db.retrieve_context(title, description)
            
            explanation = self.vuln_agent.analyze(title, description, evidence, threat_context, model_name)
            impact = self.risk_agent.assess(title, explanation, threat_context, model_name)
            rem_steps, code_patch, confidence = self.remed_agent.patch(title, evidence, model_name)
            
            return {
                "explanation": explanation,
                "business_impact": impact,
                "remediation": rem_steps,
                "code_patch": code_patch,
                "confidence": confidence
            }
        except RuntimeError:
            raise 
        except Exception as e:
            raise RuntimeError(f"AI analysis failed: {str(e)}")

    def evaluate_false_positive(self, title: str, description: str, evidence: str, provider: str = "local-llama3", api_key: str = None) -> dict:
        if "gemini" in provider.lower():
            if not api_key:
                return {"is_false_positive": False, "reason": "Gemini API Key missing. Defaulting to true positive."}
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                prompt = f"""You are GhostGraph AI's False Positive Reduction Engine.
A static analysis scanner has flagged the following code snippet. 
Your job is to determine if this is a FALSE POSITIVE (e.g., test code, a mock, unused code, or perfectly safe context) or a TRUE VULNERABILITY (dangerous code that could run in production).

CRITICAL DIRECTIVE: You must default to treating this as a TRUE VULNERABILITY (is_real_vulnerability: true). 
You may ONLY mark it as a False Positive (is_real_vulnerability: false) IF AND ONLY IF you see absolute proof in the snippet that it is safe, such as:
1. The code explicitly hardcodes a safely sanitized, static string.
2. The file path explicitly contains "test", "mock", or "spec".
3. A secret key is literally "secret", "password", "test", or similar mock data.

If a variable's origin is UNKNOWN or NOT VISIBLE in the snippet, you MUST ASSUME it is attacker-controlled and mark it as a TRUE VULNERABILITY. Do not guess that it is safe.

Title: {title}
Description: {description}
Code Snippet:
{evidence}

Analyze the code. Does this look like a real, reachable vulnerability in production logic, or is it just test data, demo secrets, or unreachable noise?
Provide your response strictly as JSON with two keys:
- "is_real_vulnerability": A boolean (true if it is a real dangerous vulnerability, false if it is safe, test code, or unreachable noise).
- "reason": A 1 sentence explanation of why.
"""
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                res = json.loads(response.text)
                is_vuln = res.get("is_real_vulnerability", True)
                if isinstance(is_vuln, str):
                    is_vuln = is_vuln.lower() == 'true'
                return {"is_false_positive": not bool(is_vuln), "reason": str(res.get("reason", ""))}
            except Exception as e:
                return {"is_false_positive": False, "reason": f"Gemini API failed: {str(e)}"}

        if "cloud" in provider.lower() or "openai" in provider.lower() or "anthropic" in provider.lower():
            if not api_key:
                return {"is_false_positive": False, "reason": "Cloud API Key missing. Defaulting to true positive."}
            return {"is_false_positive": False, "reason": "Cloud simulation assumes true positive."}

        model_name = "mistral" if "mistral" in provider else "llama3"
        available, _ = check_ollama_available(model_name)
        if not available:
             return {"is_false_positive": False, "reason": "AI offline. Defaulting to true positive."}

        prompt = f"""You are GhostGraph AI's False Positive Reduction Engine.
A static analysis scanner has flagged the following code snippet. 
Your job is to determine if this is a FALSE POSITIVE (e.g., test code, a mock, unused code, or perfectly safe context) or a TRUE VULNERABILITY (dangerous code that could run in production).

CRITICAL DIRECTIVE: You must default to treating this as a TRUE VULNERABILITY (is_real_vulnerability: true). 
You may ONLY mark it as a False Positive (is_real_vulnerability: false) IF AND ONLY IF you see absolute proof in the snippet that it is safe, such as:
1. The code explicitly hardcodes a safely sanitized, static string.
2. The file path explicitly contains "test", "mock", or "spec".
3. A secret key is literally "secret", "password", "test", or similar mock data.

If a variable's origin is UNKNOWN or NOT VISIBLE in the snippet, you MUST ASSUME it is attacker-controlled and mark it as a TRUE VULNERABILITY. Do not guess that it is safe.

Title: {title}
Description: {description}
Code Snippet:
{evidence}

Analyze the code. Does this look like a real, reachable vulnerability in production logic, or is it just test data, demo secrets, or unreachable noise?
Provide your response strictly as JSON with two keys:
- "is_real_vulnerability": A boolean (true if it is a real dangerous vulnerability, false if it is safe, test code, or unreachable noise).
- "reason": A 1 sentence explanation of why.
"""
        try:
            response = ollama.chat(model=model_name, messages=[{"role": "user", "content": prompt}], format="json")
            res = json.loads(response['message']['content'])
            
            is_vuln = res.get("is_real_vulnerability", True)
            if isinstance(is_vuln, str):
                is_vuln = is_vuln.lower() == 'true'
            
            is_fp = not bool(is_vuln)
            reason = str(res.get("reason", ""))
            return {"is_false_positive": is_fp, "reason": reason}
        except Exception:
            return {"is_false_positive": False, "reason": "AI parsing failed. Defaulting to true positive."}

ai_analyst = AISecurityOrchestrator()
