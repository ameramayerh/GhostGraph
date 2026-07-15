import json
from typing import Optional

import ollama

from .threat_intel import threat_intel_db


LOCAL_MODELS = {
    "local-llama3": "llama3",
    "local-mistral": "mistral",
}
GEMINI_PROVIDER = "gemini-2.5-flash"
SUPPORTED_LLM_PROVIDERS = frozenset([*LOCAL_MODELS, GEMINI_PROVIDER])


def check_ollama_available(model_name: str = "llama3") -> tuple[bool, str]:
    try:
        models = ollama.list()
        available = [model.model for model in models.models] if hasattr(models, "models") else []
        if not any(model.startswith(model_name) for model in available):
            return False, f"Ollama is running, but model '{model_name}' is not installed. Run: ollama pull {model_name}"
        return True, "OK"
    except Exception as error:
        return False, f"Cannot connect to Ollama: {error}"


def _gemini_client(api_key: Optional[str]):
    if not api_key:
        raise RuntimeError("A Gemini API key is required.")
    from google import genai

    return genai.Client(api_key=api_key)


class FindingExplainer:
    def analyze(self, title: str, description: str, evidence: str, threat_context: str, model: str) -> str:
        prompt = f"""You are an application-security reviewer helping a developer understand a scanner finding.

Explain the vulnerability category, identify the relevant evidence, and describe the conditions that make it risky.
Do not invent evidence or provide exploitation instructions.

Title: {title}
Description: {description}
Evidence: {evidence}
Threat-intelligence context: {threat_context}
"""
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]


class RiskAssessor:
    def assess(self, title: str, explanation: str, threat_context: str, model: str) -> str:
        prompt = f"""Summarize the likely business impact of this application-security finding in two to four sentences.
Focus on data exposure, service integrity, and operational consequences. Do not provide exploitation steps.

Title: {title}
Technical explanation: {explanation}
Threat-intelligence context: {threat_context}
"""
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]


class RemediationAdvisor:
    def patch(self, title: str, evidence: str, model: str) -> tuple[str, str, str]:
        prompt = f"""Provide defensive remediation guidance for this scanner finding.
Return JSON with the keys remediation_steps, code_patch, and confidence_level.

Title: {title}
Evidence: {evidence}
"""
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], format="json")
        try:
            result = json.loads(response["message"]["content"])
            remediation = result.get("remediation_steps", "")
            patch = result.get("code_patch", "")
            if isinstance(remediation, (list, dict)):
                remediation = json.dumps(remediation, indent=2)
            if isinstance(patch, (list, dict)):
                patch = json.dumps(patch, indent=2)
            return str(remediation), str(patch), str(result.get("confidence_level", "Unknown"))
        except json.JSONDecodeError:
            return "Review the secure coding guidance for this framework.", "No patch generated.", "Low"


class AIAnalysisService:
    def __init__(self):
        self.explainer = FindingExplainer()
        self.risk_assessor = RiskAssessor()
        self.remediation_advisor = RemediationAdvisor()

    @staticmethod
    def _local_model(provider: str) -> str:
        try:
            return LOCAL_MODELS[provider]
        except KeyError as error:
            raise RuntimeError(f"Unsupported AI provider: {provider}") from error

    def provider_available(self, provider: str, api_key: Optional[str] = None) -> tuple[bool, str]:
        if provider == GEMINI_PROVIDER:
            return (True, "OK") if api_key else (False, "A Gemini API key is not configured.")
        if provider in LOCAL_MODELS:
            return check_ollama_available(LOCAL_MODELS[provider])
        return False, f"Unsupported AI provider: {provider}"

    def generate(self, prompt: str, provider: str = "local-llama3", api_key: Optional[str] = None) -> str:
        if provider == GEMINI_PROVIDER:
            try:
                response = _gemini_client(api_key).models.generate_content(
                    model="gemini-2.5-flash", contents=prompt
                )
                return response.text or "[]"
            except Exception as error:
                raise RuntimeError(f"Gemini request failed: {error}") from error

        model = self._local_model(provider)
        available, message = check_ollama_available(model)
        if not available:
            raise RuntimeError(message)
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"]

    def analyze_finding(
        self,
        title: str,
        description: str,
        evidence: str,
        provider: str = "local-llama3",
        api_key: Optional[str] = None,
    ) -> dict:
        if provider == GEMINI_PROVIDER:
            prompt = f"""Analyze this application-security finding and return JSON with the keys explanation,
business_impact, remediation, code_patch, and confidence.

Title: {title}
Description: {description}
Evidence: {evidence}
"""
            try:
                from google.genai import types

                response = _gemini_client(api_key).models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                result = json.loads(response.text)
                return {
                    "explanation": str(result.get("explanation", "")),
                    "business_impact": str(result.get("business_impact", "")),
                    "remediation": str(result.get("remediation", "")),
                    "code_patch": str(result.get("code_patch", "")),
                    "confidence": str(result.get("confidence", "Unknown")),
                }
            except Exception as error:
                raise RuntimeError(f"Gemini request failed: {error}") from error

        model = self._local_model(provider)
        available, message = check_ollama_available(model)
        if not available:
            raise RuntimeError(message)

        try:
            context = threat_intel_db.retrieve_context(title, description)
            explanation = self.explainer.analyze(title, description, evidence, context, model)
            impact = self.risk_assessor.assess(title, explanation, context, model)
            remediation, code_patch, confidence = self.remediation_advisor.patch(title, evidence, model)
            return {
                "explanation": explanation,
                "business_impact": impact,
                "remediation": remediation,
                "code_patch": code_patch,
                "confidence": confidence,
            }
        except Exception as error:
            raise RuntimeError(f"AI analysis failed: {error}") from error

    def evaluate_false_positive(
        self,
        title: str,
        description: str,
        evidence: str,
        provider: str = "local-llama3",
        api_key: Optional[str] = None,
    ) -> dict:
        prompt = f"""Review this static-analysis finding conservatively.
Return JSON with is_real_vulnerability (boolean) and reason (one sentence).
Treat the finding as real unless the evidence clearly proves it is test-only, unreachable, or safely sanitized.

Title: {title}
Description: {description}
Evidence: {evidence}
"""

        try:
            if provider == GEMINI_PROVIDER:
                from google.genai import types

                response = _gemini_client(api_key).models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                result = json.loads(response.text)
            else:
                model = self._local_model(provider)
                available, _ = check_ollama_available(model)
                if not available:
                    return {"is_false_positive": False, "reason": "AI provider unavailable; retained for human review."}
                response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], format="json")
                result = json.loads(response["message"]["content"])

            is_real = result.get("is_real_vulnerability", True)
            if isinstance(is_real, str):
                is_real = is_real.lower() == "true"
            return {"is_false_positive": not bool(is_real), "reason": str(result.get("reason", ""))}
        except Exception as error:
            return {"is_false_positive": False, "reason": f"AI review unavailable; retained for human review. ({error})"}


ai_analyst = AIAnalysisService()
