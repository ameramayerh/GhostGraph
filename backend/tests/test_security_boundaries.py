import asyncio
import zipfile
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from app.api import extract_zip_safely
from app.services.ai import SUPPORTED_LLM_PROVIDERS, ai_analyst
from app.services.report_generator import classify_attack, generate_pdf_report
from main import app


def test_health_endpoint() -> None:
    async def request_health():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.get("/api/health")

    response = asyncio.run(request_health())
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ghostgraph"}


def test_safe_zip_extracts_inside_destination(tmp_path) -> None:
    archive_path = tmp_path / "safe.zip"
    destination = tmp_path / "output"
    destination.mkdir()

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("src/app.js", "console.log('safe');")

    extract_zip_safely(str(archive_path), str(destination))

    assert (destination / "src" / "app.js").read_text(encoding="utf-8") == "console.log('safe');"


def test_zip_path_traversal_is_rejected(tmp_path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    destination = tmp_path / "output"
    destination.mkdir()

    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "not allowed")

    with pytest.raises(HTTPException) as error:
        extract_zip_safely(str(archive_path), str(destination))

    assert error.value.status_code == 400
    assert not (tmp_path / "outside.txt").exists()


def test_ai_provider_registry_rejects_unknown_provider() -> None:
    assert SUPPORTED_LLM_PROVIDERS == {
        "local-llama3",
        "local-mistral",
        "gemini-2.5-flash",
    }
    available, message = ai_analyst.provider_available("unimplemented-provider")
    assert available is False
    assert "Unsupported AI provider" in message


@pytest.mark.parametrize(
    ("rule_id", "expected_attack_type"),
    [
        ("ghostgraph.javascript.eval", "JavaScript Code Injection"),
        ("ghostgraph.javascript.child-process-exec", "Operating-System Command Injection"),
        ("ghostgraph.javascript.unsafe-innerhtml", "Cross-Site Scripting (XSS)"),
        ("ghostgraph.javascript.hardcoded-secret", "Credential or Secret Exposure"),
        ("npm-audit-cve", "Known Vulnerable Component"),
    ],
)
def test_report_classifies_attack_types(rule_id: str, expected_attack_type: str) -> None:
    finding = SimpleNamespace(
        semgrep_rule_id=rule_id,
        title="Cross-site scripting advisory" if rule_id == "npm-audit-cve" else "Finding",
        description="Description",
        category="Static Analysis",
    )

    assert classify_attack(finding).attack_type == expected_attack_type


def test_pdf_report_renders_attack_context_without_ai() -> None:
    engagement = SimpleNamespace(
        name="Demo & Review",
        scope="Authorized source-code review",
        authorized_by="Student",
        total_findings=1,
        filtered_findings=0,
    )
    finding = SimpleNamespace(
        title="Unsafe InnerHTML",
        description="Dynamic content is written to innerHTML.",
        file_path="src/app.js",
        line_number=12,
        code_snippet="element.innerHTML = input;",
        semgrep_rule_id="ghostgraph.javascript.unsafe-innerhtml",
        severity="Medium",
        category="Static Analysis",
        ai_explanation=None,
        business_impact=None,
        remediation=None,
        code_patch=None,
        is_false_positive=False,
        filtering_status="Not Run",
    )

    report = generate_pdf_report(engagement, [finding], [])

    assert report.read(4) == b"%PDF"
