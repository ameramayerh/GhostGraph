# GhostGraph

GhostGraph is a desktop application-security toolkit. Upload a ZIP of a project and it combines dependency auditing, static analysis, and optional AI review to help developers find and understand security issues before release.

## What it scans

- **SCA:** `npm audit` identifies vulnerable JavaScript dependencies.
- **SAST:** Semgrep checks source files against security-focused rules.
- **Optional AI-assisted review:** Ollama (local) or Gemini can review selected security-sensitive files and explain existing findings.
- **Human verification:** AI output is advisory; rule-based findings remain available when AI is disabled or unavailable.

Results are stored in SQLite. The UI includes engagement history, analytics, live scan logs, a local Chroma threat-intelligence viewer, and PDF export.

## Architecture

| Component | Responsibility |
| --- | --- |
| Electron | Opens the Windows desktop window and starts the local API when needed |
| React + Vite | Renders engagements, findings, analytics, settings, and reports |
| FastAPI | Validates uploads, coordinates scans, and exposes local API endpoints |
| Semgrep | Runs the bundled GhostGraph static-analysis rules |
| npm audit | Checks JavaScript dependencies against npm advisories |
| SQLModel + SQLite | Persists engagements, findings, settings, and audit events |
| ChromaDB | Stores a small local collection of defensive security guidance |
| ReportLab | Generates the PDF scan report |

The core scan does not require an AI provider. Supported optional providers are Ollama with `llama3` or `mistral`, and Google Gemini 2.5 Flash.

## Run the desktop app

Prerequisites: Python 3.11+, Node.js 20+, and npm. Ollama is optional unless you select a local AI provider.

Set up the backend environment once:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Install the desktop dependencies once, then start GhostGraph:

```powershell
cd frontend
npm install
npm run desktop
```

Electron opens GhostGraph in its own desktop window and starts the local FastAPI backend automatically when port 8000 is available.

## Run with Docker

Prerequisites: Docker Desktop. Install and start [Ollama](https://ollama.com/) with `ollama pull llama3` if you want local AI features.

```bash
docker compose up --build
```

Open the frontend at `http://localhost:8080`. The API documentation is at `http://localhost:8000/docs`.

The Docker volumes retain the SQLite database and vector database between restarts. `npm audit` runs inside the backend container, so Node.js is included in that image.

## Run locally for development

Prerequisites: Python 3.11+, Node.js 20+, and npm. Ollama is optional unless you select a local AI provider.

```bash
# Terminal 1: backend
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

```bash
# Terminal 2: frontend
cd frontend
npm install
npm run dev
```

Vite prints the local frontend URL, normally `http://localhost:5173`.

Set `VITE_API_URL` before starting the frontend if the API is hosted somewhere other than `http://127.0.0.1:8000`.

## Use the app

1. Create a project scan and record the authorized person and scope.
2. Open that engagement and upload a source-code ZIP (maximum 100 MB; extracted content maximum 500 MB).
3. Watch the live terminal while SCA, SAST, and optional AI checks run.
4. Review findings, request an AI explanation when needed, and download the PDF report.

## Security boundaries

- Scans require an engagement with an authorization contact and defined scope.
- ZIP uploads are limited to 100 MB and extracted content is limited to 500 MB.
- Archive members are resolved before extraction to reject path traversal.
- Uploaded application code is inspected, not executed.
- Settings responses report whether an API key exists without returning the key itself.
- CORS defaults to the Electron renderer and documented local development origins.

## Tests

Install development dependencies and run the focused backend tests:

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
cd backend
.venv\Scripts\python.exe -m pytest -q
```

Validate the scanner rules and frontend build:

```powershell
backend\.venv\Scripts\semgrep.exe --validate --config backend\app\services\rules\ghostgraph.yml
cd frontend
npm run build
```

## Notes

- The app is designed for local, authorized source-code assessment. It does not provide user authentication or multi-user access control.
- Local AI requires Ollama plus the selected model. Gemini requires a key configured through the Settings page.
- The bundled Semgrep rules and built-in threat-intelligence guidance work offline. `npm audit` requires access to the npm advisory service.
- GhostGraph is a focused graduation-project prototype, not a replacement for a penetration test or enterprise SAST platform.
- The bundled static-analysis rules currently target JavaScript and TypeScript patterns demonstrated by the included sample.
- AI output may be incomplete or incorrect and must be verified by a human reviewer.
- API keys are stored in the local SQLite database; a production version should use operating-system credential storage or encryption at rest.
