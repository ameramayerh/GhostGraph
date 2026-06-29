# GhostGraph

GhostGraph is an open-source Static Application Security Testing (SAST) and Software Composition Analysis (SCA) platform. It provides a clean, modern interface to run standard security tools against your code and track the findings in a local database.

## Key Features

*   **Multi-Engine Scanning**: Extracts and scans uploaded ZIP repositories using `semgrep` for SAST and `npm audit` for SCA.
*   **Live Telemetry**: A real-time terminal built into the UI that intercepts and streams raw Uvicorn REST traffic and SQLAlchemy database queries via WebSockets.
*   **Analytics Dashboard**: Visual reporting using Recharts to track scan metrics and severity distributions.
*   **Dockerized Environment**: Containerized frontend and backend for seamless, cross-platform deployment.

---

## Tech Stack

*   **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts.
*   **Backend**: Python, FastAPI, SQLModel (SQLite), Uvicorn, WebSockets.
*   **Security Engines**: Semgrep, NPM Audit.

---

## How to Run the App

GhostGraph is now fully containerized using Docker.

### Running with Docker Compose
1. Ensure you have Docker and Docker Compose installed on your system.
2. Open a terminal in the root of the GhostGraph directory.
3. Run the following command to build and start the containers:
   ```bash
   docker-compose up --build
   ```
4. Once the containers are running, open your browser and navigate to `http://localhost` to access the frontend, and `http://localhost:8000` for the backend API.

---

## Usage Guide

1. **Dashboard Overview**: When you open the app, you will see a list of active engagements (projects).
2. **Create an Engagement**: Click "New Project Scan" to define a scope and authorize a scan.
3. **Upload Source Code**: Navigate into the engagement and use the **"Upload & Scan Source ZIP"** button to upload a repository.
4. **Watch the Terminal**: As the scan runs, watch the **Live Terminal** stream real-time database queries and scan execution logs.
5. **Review Findings**: Once the scan finishes, review the flagged vulnerabilities in the findings list.
6. **Export**: Click "Export Report" to download a clean PDF summary of the engagement.
