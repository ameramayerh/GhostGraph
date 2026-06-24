# GhostGraph

GhostGraph is an open-source Static Application Security Testing (SAST) and Software Composition Analysis (SCA) platform. It provides a clean, modern interface to run standard security tools against your code and track the findings in a local database.

## Key Features

*   **Multi-Engine Scanning**: Extracts and scans uploaded ZIP repositories using `semgrep` for SAST and `npm audit` for SCA.
*   **Live Telemetry**: A real-time terminal built into the UI that intercepts and streams raw Uvicorn REST traffic and SQLAlchemy database queries via WebSockets.
*   **Analytics Dashboard**: Visual reporting using Recharts to track scan metrics and severity distributions.
*   **Cross-Platform Support**: Designed to run natively on Windows or within a Kali Linux VM.

---

## Tech Stack

*   **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts.
*   **Backend**: Python, FastAPI, SQLModel (SQLite), Uvicorn, WebSockets.
*   **Security Engines**: Semgrep, NPM Audit.

---

## How to Run the App

We have provided convenient launcher scripts that handle virtual environments, dependency installations, and port forwarding for you.

### Option 1: Running on Windows
1. Double-click the **`start_ghostgraph.bat`** file located in the root of the project.
2. The script will automatically open the backend and frontend terminals and launch your browser to `http://localhost:5173`.

### Option 2: Running on Linux (e.g. Kali VM)
1. Open a terminal in the GhostGraph directory.
2. Run the launcher script:
   ```bash
   chmod +x start_ghostgraph.sh
   ./start_ghostgraph.sh
   ```

---

## Usage Guide

1. **Dashboard Overview**: When you open the app, you will see a list of active engagements (projects).
2. **Create an Engagement**: Click "New Project Scan" to define a scope and authorize a scan.
3. **Upload Source Code**: Navigate into the engagement and use the **"Upload & Scan Source ZIP"** button to upload a repository.
4. **Watch the Terminal**: As the scan runs, watch the **Live Terminal** stream real-time database queries and scan execution logs.
5. **Review Findings**: Once the scan finishes, review the flagged vulnerabilities in the findings list.
6. **Export**: Click "Export Report" to download a clean PDF summary of the engagement.
