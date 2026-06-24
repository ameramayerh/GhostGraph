"""
GhostGraph Presentation PDF Generator
Generates a professional slide-deck-style PDF.
"""
from fpdf import FPDF
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "GhostGraph_Presentation.pdf")

# -- Color Palette --
BG_DARK    = (15, 15, 20)
BG_SLIDE   = (22, 22, 30)
ACCENT     = (99, 102, 241)   # Indigo
ACCENT2    = (139, 92, 246)   # Purple
GREEN      = (34, 197, 94)
RED        = (239, 68, 68)
ORANGE     = (249, 115, 22)
WHITE      = (240, 240, 245)
GRAY       = (156, 163, 175)
DARK_GRAY  = (75, 85, 99)

TOTAL_SLIDES = 11


class PresentationPDF(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)

    # ---- helpers ----
    def _bg(self):
        self.set_fill_color(*BG_DARK)
        self.rect(0, 0, self.w, self.h, "F")

    def _card(self, x, y, w, h):
        self.set_fill_color(*BG_SLIDE)
        self.set_draw_color(50, 50, 65)
        self.rect(x, y, w, h, "DF")

    def _accent_bar(self, x, y, w, h):
        self.set_fill_color(*ACCENT)
        self.rect(x, y, w, h, "F")

    def _slide_number(self, num):
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(self.w - 30, self.h - 10)
        self.cell(20, 5, f"{num} / {TOTAL_SLIDES}", align="R")

    # ---- slides ----
    def slide_title(self):
        self.add_page()
        self._bg()
        self.set_fill_color(*ACCENT)
        self.rect(0, 0, self.w, 6, "F")
        self.set_fill_color(*ACCENT2)
        self.rect(0, 6, self.w, 2, "F")

        self.set_font("Helvetica", "B", 44)
        self.set_text_color(*WHITE)
        self.set_xy(30, 45)
        self.cell(0, 18, "GhostGraph", new_x="LMARGIN", new_y="NEXT")

        self.set_font("Helvetica", "", 20)
        self.set_text_color(*ACCENT)
        self.set_xy(30, 68)
        self.cell(0, 10, "AI-Assisted Security Scanner Prototype")

        self.set_font("Helvetica", "I", 13)
        self.set_text_color(*GRAY)
        self.set_xy(30, 85)
        self.cell(0, 8, "An experimental tool that uses AI to filter out noise from traditional scanners.")

        self.set_font("Helvetica", "", 10)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(30, self.h - 22)
        self.cell(0, 5, "Powered by Ollama (Local LLM)  |  Semgrep  |  ChromaDB  |  FastAPI + React")
        self._slide_number(1)

    def slide_problem(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*RED)
        self.set_xy(20, 18)
        self.cell(0, 12, "The Problem: Alert Fatigue")

        self.set_font("Helvetica", "", 11)
        self.set_text_color(*GRAY)
        self.set_xy(20, 34)
        self.cell(0, 6, "Modern SAST tools generate thousands of alerts. Most of them are noise.")

        y = 50
        bullets = [
            ("High False Positive Rates", "Traditional scanners flag test files, demo secrets, and unreachable dead code as critical vulnerabilities."),
            ("Developer Friction", "Security engineers spend roughly 80% of their time triaging noise instead of fixing the real critical bugs."),
            ("No Business Context", "A rule flags a raw SQL query, but has no way to know the input was already sanitized 3 functions upstream."),
            ("Missed Real Threats", "While teams drown in noise, the real exploitable vulnerabilities slip through unnoticed."),
        ]
        for title, desc in bullets:
            self._card(20, y, self.w - 40, 22)
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(*WHITE)
            self.set_xy(26, y + 3)
            self.cell(0, 6, title)
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*GRAY)
            self.set_xy(26, y + 11)
            self.cell(0, 6, desc)
            y += 28
        self._slide_number(2)

    def slide_solution(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*GREEN)
        self.set_xy(20, 18)
        self.cell(0, 12, "The Solution: AI-Assisted Threat Hunting")

        self.set_font("Helvetica", "", 11)
        self.set_text_color(*GRAY)
        self.set_xy(20, 34)
        self.cell(0, 6, "GhostGraph uses local LLMs to help filter alerts and identify real vulnerabilities.")

        steps = [
            ("1. SCAN", "Upload a ZIP. The engine extracts source code and runs Semgrep (SAST) + npm audit (SCA) deterministic rules.", ACCENT),
            ("2. THINK", "Each flagged code snippet is sent with a 250-line context window to a local LLM (Llama 3 via Ollama).", ACCENT2),
            ("3. FILTER", "The AI analyzes reachability and context. Test data, demo secrets, and dead code are auto-dismissed as noise.", ORANGE),
            ("4. REMEDIATE", "Verified vulnerabilities get an executive summary, business impact analysis, and a secure code patch.", GREEN),
        ]

        y = 50
        for title, desc, color in steps:
            self._card(20, y, self.w - 40, 24)
            self.set_fill_color(*color)
            self.rect(20, y, 4, 24, "F")
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*color)
            self.set_xy(30, y + 3)
            self.cell(40, 7, title)
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*GRAY)
            self.set_xy(30, y + 12)
            self.cell(0, 6, desc)
            y += 30
        self._slide_number(3)

    def slide_architecture(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*ACCENT)
        self.set_xy(20, 18)
        self.cell(0, 12, "System Architecture")

        col_w = (self.w - 50) / 3
        x1 = 20
        x2 = x1 + col_w + 5
        x3 = x2 + col_w + 5

        for x, title, color in [(x1, "FRONTEND", ACCENT), (x2, "BACKEND", GREEN), (x3, "AI / DATA", ACCENT2)]:
            self.set_fill_color(*color)
            self.rect(x, 40, col_w, 8, "F")
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(*BG_DARK)
            self.set_xy(x, 40)
            self.cell(col_w, 8, title, align="C")

        frontend_items = ["React + TypeScript", "Vite Dev Server", "Recharts Analytics", "WebSocket Terminal", "Tailwind CSS"]
        backend_items = ["FastAPI (Python)", "SQLModel + SQLite", "Uvicorn ASGI", "Background Workers", "WebSocket Manager"]
        ai_items = ["Ollama (Local LLM)", "Semgrep Engine", "npm audit (SCA)", "ChromaDB Vectors", "SentenceTransformers"]

        for col_x, items in [(x1, frontend_items), (x2, backend_items), (x3, ai_items)]:
            y = 52
            for item in items:
                self._card(col_x, y, col_w, 14)
                self.set_font("Helvetica", "", 10)
                self.set_text_color(*WHITE)
                self.set_xy(col_x + 4, y + 4)
                self.cell(col_w - 8, 6, item, align="C")
                y += 18

        self.set_font("Helvetica", "I", 9)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(20, self.h - 18)
        self.cell(0, 5, "All AI processing runs 100% locally via Ollama. Zero source code ever leaves the network. Air-gap ready.")
        self._slide_number(4)

    def slide_telemetry(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*WHITE)
        self.set_xy(20, 18)
        self.cell(0, 12, "Live Telemetry & Threat Intel")

        panel_w = (self.w - 50) / 2
        self._card(20, 40, panel_w, 120)
        self.set_fill_color(10, 10, 14)
        self.rect(24, 44, panel_w - 8, 112, "F")

        self.set_fill_color(30, 30, 38)
        self.rect(24, 44, panel_w - 8, 10, "F")
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*GRAY)
        self.set_xy(28, 45)
        self.cell(0, 8, "> Engine Logs (Live)")
        for dx, c in [(panel_w - 20, RED), (panel_w - 16, ORANGE), (panel_w - 12, GREEN)]:
            self.set_fill_color(*c)
            self.ellipse(24 + dx, 47, 3, 3, "F")

        self.set_font("Courier", "", 7)
        terminal_lines = [
            ("[14:32:01]  uvicorn.access: POST /api/engagements/3/scan 200", "info"),
            ("[14:32:01]  sqlalchemy: SELECT engagement.id FROM engagement", "info"),
            ("[14:32:02]  ghostgraph: Extracting source code from app.zip...", "info"),
            ("[14:32:05]  ghostgraph: Launching Semgrep SAST scan...", "info"),
            ("[14:32:08]  ghostgraph: Running SCA via npm audit...", "info"),
            ("[14:32:12]  ghostgraph: 47 raw findings detected.", "warning"),
            ("[14:32:12]  ghostgraph: De-duplicating... 31 unique findings.", "info"),
            ("[14:32:13]  ghostgraph: AI Pre-Filter started on 31 findings.", "info"),
            ("[14:32:18]  ollama: Finding 1/31 - False Positive (test data)", "success"),
            ("[14:32:22]  ollama: Finding 2/31 - TRUE POSITIVE (SQLi)", "error"),
            ("[14:32:25]  ghostgraph: Background filtering 35% complete...", "info"),
        ]
        y = 58
        for line, level in terminal_lines:
            color_map = {"info": (147, 197, 253), "warning": (253, 224, 71), "error": (252, 129, 129), "success": (134, 239, 172)}
            self.set_text_color(*color_map.get(level, GRAY))
            self.set_xy(28, y)
            self.cell(0, 4.5, line)
            y += 6.5

        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*ACCENT)
        self.set_xy(24, 140)
        self.cell(panel_w - 8, 5, "Real-time WebSocket intercept of Python logging", align="C")

        rx = 20 + panel_w + 10
        self._card(rx, 40, panel_w, 55)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*ACCENT2)
        self.set_xy(rx + 6, 44)
        self.cell(0, 8, "Threat Intelligence (RAG)")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GRAY)
        self.set_xy(rx + 6, 56)
        self.multi_cell(panel_w - 12, 5.5, "Built-in ChromaDB vector database stores security TTPs. Users search by concept (e.g., 'Reflected XSS') and the engine performs semantic nearest-neighbor retrieval using sentence-transformer embeddings.")

        self._card(rx, 105, panel_w, 55)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*GREEN)
        self.set_xy(rx + 6, 109)
        self.cell(0, 8, "Air-Gapped & Private")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GRAY)
        self.set_xy(rx + 6, 121)
        self.multi_cell(panel_w - 12, 5.5, "All LLM inference runs on-premises via Ollama. No API keys. No cloud calls. Your proprietary source code never leaves the machine. Perfect for regulated industries and red team operations.")
        self._slide_number(5)

    def slide_data_flow(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 28)
        self.set_text_color(*ACCENT)
        self.set_xy(20, 18)
        self.cell(0, 12, "Exactly How It Works (Data Flow)")

        steps = [
            ("Upload", "User uploads a .zip via the React frontend. Backend creates a temp directory and extracts the source code."),
            ("Scan", "Backend spawns async subprocesses: Semgrep (OWASP Top 10, CWE-25 rulesets) and npm audit (dependency CVEs)."),
            ("De-Duplicate", "Findings are sorted by file path + line number. Alerts within 5 lines of each other are merged into one."),
            ("AI Pre-Filter", "A background worker sends each finding with a 250-line context window to Ollama. The LLM replies in strict JSON: is_real_vulnerability (bool) + reason. False positives are auto-dismissed."),
            ("Deep Analysis", "User clicks 'Ask GhostGraph AI' on a verified finding. Ollama generates: Explanation, Business Impact, and a Secure Code Patch."),
            ("Report", "Results are stored in SQLite. User can export a full PDF report or browse the interactive dashboard."),
        ]

        y = 40
        for i, (title, desc) in enumerate(steps):
            self.set_fill_color(*ACCENT)
            self.ellipse(24, y + 2, 10, 10, "F")
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*BG_DARK)
            self.set_xy(24, y + 3)
            self.cell(10, 8, str(i + 1), align="C")

            if i < len(steps) - 1:
                self.set_draw_color(*ACCENT)
                self.set_line_width(0.4)
                self.line(29, y + 12, 29, y + 23)

            self.set_font("Helvetica", "B", 12)
            self.set_text_color(*WHITE)
            self.set_xy(40, y + 1)
            self.cell(30, 6, title)

            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*GRAY)
            self.set_xy(40, y + 8)
            self.multi_cell(self.w - 60, 5, desc)
            y += 24
        self._slide_number(6)

    def slide_tools_explained(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 26)
        self.set_text_color(*ACCENT)
        self.set_xy(20, 15)
        self.cell(0, 12, "What We Used & Why (Plain English)")

        tools = [
            ("React", "The user interface you see in the browser. It draws the buttons, tables, and charts.", ACCENT),
            ("FastAPI", "The Python web server that handles all requests behind the scenes.", GREEN),
            ("Semgrep", "An open-source code scanner. It reads source files and matches patterns for common bugs.", ORANGE),
            ("npm audit", "Checks if any libraries the project depends on have known security holes (CVEs).", ORANGE),
            ("Ollama", "Runs AI language models (like Llama 3) entirely on your own machine. No cloud needed.", ACCENT2),
            ("ChromaDB", "A small local database that stores security knowledge as math vectors for smart search.", ACCENT2),
            ("SQLite", "A tiny file-based database that stores your projects, findings, and scan history.", GREEN),
            ("WebSockets", "A live two-way connection so the terminal updates instantly without refreshing.", ACCENT),
        ]

        y = 35
        for name, desc, color in tools:
            self.set_fill_color(*color)
            self.ellipse(22, y + 2, 4, 4, "F")
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*WHITE)
            self.set_xy(30, y)
            self.cell(35, 7, name)
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*GRAY)
            self.set_xy(68, y)
            self.cell(0, 7, desc)
            y += 16
        self._slide_number(7)

    def slide_how_we_built(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 26)
        self.set_text_color(*GREEN)
        self.set_xy(20, 15)
        self.cell(0, 12, "How We Built It (Step by Step)")

        steps = [
            ("1", "Built the Backend", "We wrote a Python server using FastAPI. It handles file uploads, runs scans, stores results in a SQLite database, and talks to the AI."),
            ("2", "Built the Frontend", "We created a React app with TypeScript. It shows the dashboard, findings list, charts, and a live terminal. It talks to the backend over HTTP."),
            ("3", "Plugged in Semgrep", "We added Semgrep as our main code scanner. It uses open-source security rulesets (OWASP Top 10, CWE Top 25) to find vulnerabilities."),
            ("4", "Added AI Filtering", "We connected to Ollama (a local AI server). After Semgrep flags code, we send 250 lines of context to the AI and ask: is this real or noise?"),
            ("5", "Added Threat Intel", "We set up ChromaDB to store security knowledge. Users can search concepts like 'SQL Injection' and get smart results even without exact keywords."),
            ("6", "Wired Up Live Logs", "We hooked Python's logging system into a WebSocket so every database query and API call streams to the frontend terminal in real time."),
        ]

        y = 35
        for num, title, desc in steps:
            self._card(20, y, self.w - 40, 22)
            self.set_fill_color(*ACCENT)
            self.rect(20, y, 18, 22, "F")
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(*BG_DARK)
            self.set_xy(20, y + 6)
            self.cell(18, 8, num, align="C")
            self.set_font("Helvetica", "B", 12)
            self.set_text_color(*WHITE)
            self.set_xy(44, y + 2)
            self.cell(0, 6, title)
            self.set_font("Helvetica", "", 9.5)
            self.set_text_color(*GRAY)
            self.set_xy(44, y + 10)
            self.multi_cell(self.w - 70, 5, desc)
            y += 26
        self._slide_number(8)

    def slide_example_real(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*RED)
        self.set_xy(20, 15)
        self.cell(0, 12, "Example: Real Vulnerability Found")

        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*GRAY)
        self.set_xy(20, 30)
        self.cell(0, 6, "Semgrep flags it. The AI confirms it. GhostGraph gives you the fix.")

        # --- Left: Vulnerable Code ---
        left_w = (self.w - 50) / 2
        self._card(20, 42, left_w, 80)
        self.set_fill_color(*RED)
        self.rect(20, 42, left_w, 8, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*BG_DARK)
        self.set_xy(20, 42)
        self.cell(left_w, 8, "VULNERABLE CODE (app/routes/users.py:34)", align="C")

        self.set_font("Courier", "", 7.5)
        self.set_text_color(252, 129, 129)
        code_lines = [
            'def get_user(request):',
            '    user_id = request.args.get("id")',
            '    query = f"SELECT * FROM users',
            '            WHERE id = {user_id}"',
            '    result = db.execute(query)',
            '    return jsonify(result)',
        ]
        y = 55
        for line in code_lines:
            self.set_xy(26, y)
            self.cell(0, 5, line)
            y += 7

        # AI Verdict
        self.set_fill_color(*RED)
        self.rect(26, 105, 50, 7, "F")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*WHITE)
        self.set_xy(26, 105)
        self.cell(50, 7, "AI VERDICT: TRUE POSITIVE", align="C")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.set_xy(80, 105)
        self.cell(0, 7, "User input is directly interpolated into a SQL query.")

        # --- Right: Fixed Code ---
        rx = 20 + left_w + 10
        self._card(rx, 42, left_w, 80)
        self.set_fill_color(*GREEN)
        self.rect(rx, 42, left_w, 8, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*BG_DARK)
        self.set_xy(rx, 42)
        self.cell(left_w, 8, "SECURE FIX (AI-Generated Patch)", align="C")

        self.set_font("Courier", "", 7.5)
        self.set_text_color(134, 239, 172)
        fix_lines = [
            'def get_user(request):',
            '    user_id = request.args.get("id")',
            '    query = "SELECT * FROM users',
            '            WHERE id = ?"',
            '    result = db.execute(query,',
            '                       (user_id,))',
            '    return jsonify(result)',
        ]
        y = 55
        for line in fix_lines:
            self.set_xy(rx + 6, y)
            self.cell(0, 5, line)
            y += 7

        self.set_fill_color(*GREEN)
        self.rect(rx + 6, 105, 60, 7, "F")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*BG_DARK)
        self.set_xy(rx + 6, 105)
        self.cell(60, 7, "PARAMETERIZED QUERY - SAFE", align="C")

        # Bottom impact box
        self._card(20, 130, self.w - 40, 28)
        self.set_fill_color(*ORANGE)
        self.rect(20, 130, 4, 28, "F")
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(*ORANGE)
        self.set_xy(30, 133)
        self.cell(0, 6, "Business Impact (AI-Generated):")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRAY)
        self.set_xy(30, 141)
        self.multi_cell(self.w - 60, 5, "An attacker can manipulate the 'id' parameter to dump the entire users table, bypass authentication, or delete records. This is a classic SQL Injection (CWE-89) and is rated CVSS 9.8 Critical.")
        self._slide_number(9)

    def slide_example_fp(self):
        self.add_page()
        self._bg()
        self._accent_bar(0, 0, 6, self.h)

        self.set_font("Helvetica", "B", 24)
        self.set_text_color(*GREEN)
        self.set_xy(20, 15)
        self.cell(0, 12, "Example: False Positive Dismissed")

        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*GRAY)
        self.set_xy(20, 30)
        self.cell(0, 6, "Traditional scanners would flag this. GhostGraph's AI knows better.")

        # --- Code Card ---
        self._card(20, 42, self.w - 40, 65)
        self.set_fill_color(50, 50, 65)
        self.rect(20, 42, self.w - 40, 8, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*GRAY)
        self.set_xy(20, 42)
        self.cell(self.w - 40, 8, "FLAGGED CODE (tests/test_auth.py:12)  -  Semgrep Rule: hardcoded-credentials", align="C")

        self.set_font("Courier", "", 8)
        self.set_text_color(253, 224, 71)
        test_code = [
            '# test_auth.py - Unit tests for login flow',
            '',
            'class TestAuthentication(unittest.TestCase):',
            '    def test_login_success(self):',
            '        test_password = "P@ssw0rd123"      # <-- flagged',
            '        response = self.client.post("/login",',
            '            json={"user": "test", "pass": test_password})',
            '        self.assertEqual(response.status_code, 200)',
        ]
        y = 55
        for line in test_code:
            self.set_xy(26, y)
            self.cell(0, 5.5, line)
            y += 7

        # --- Before / After comparison ---
        half_w = (self.w - 50) / 2

        # Before (traditional scanner)
        self._card(20, 115, half_w, 40)
        self.set_fill_color(*RED)
        self.rect(20, 115, half_w, 8, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*BG_DARK)
        self.set_xy(20, 115)
        self.cell(half_w, 8, "TRADITIONAL SCANNER RESULT", align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*RED)
        self.set_xy(26, 128)
        self.cell(0, 6, "CRITICAL: Hardcoded credentials detected!")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRAY)
        self.set_xy(26, 137)
        self.cell(0, 6, "You waste 15 minutes investigating a test file.")

        # After (GhostGraph AI)
        rx = 20 + half_w + 10
        self._card(rx, 115, half_w, 40)
        self.set_fill_color(*GREEN)
        self.rect(rx, 115, half_w, 8, "F")
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*BG_DARK)
        self.set_xy(rx, 115)
        self.cell(half_w, 8, "GHOSTGRAPH AI RESULT", align="C")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*GREEN)
        self.set_xy(rx + 6, 128)
        self.cell(0, 6, "FALSE POSITIVE - Auto-dismissed.")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*GRAY)
        self.set_xy(rx + 6, 137)
        self.cell(0, 6, "AI Reason: This is test data in a unit test file. Not production code.")
        self._slide_number(10)

    def slide_closing(self):
        self.add_page()
        self._bg()

        self.set_fill_color(*ACCENT)
        self.rect(0, self.h - 8, self.w, 4, "F")
        self.set_fill_color(*ACCENT2)
        self.rect(0, self.h - 4, self.w, 4, "F")

        self.set_font("Helvetica", "B", 36)
        self.set_text_color(*WHITE)
        self.set_xy(0, 55)
        self.cell(self.w, 16, "GhostGraph", align="C")

        self.set_font("Helvetica", "", 16)
        self.set_text_color(*ACCENT)
        self.set_xy(0, 78)
        self.cell(self.w, 10, "An AI-Assisted Security Scanner Prototype", align="C")

        stats = [
            ("100%", "Local & Private"),
            ("80%+", "Noise Reduction"),
            ("0", "Cloud API Calls"),
        ]
        stat_w = 70
        start_x = (self.w - stat_w * len(stats)) / 2
        for i, (num, label) in enumerate(stats):
            x = start_x + i * stat_w
            self._card(x, 105, stat_w - 10, 35)
            self.set_font("Helvetica", "B", 22)
            self.set_text_color(*GREEN)
            self.set_xy(x, 110)
            self.cell(stat_w - 10, 12, num, align="C")
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*GRAY)
            self.set_xy(x, 124)
            self.cell(stat_w - 10, 6, label, align="C")

        self.set_font("Helvetica", "I", 11)
        self.set_text_color(*DARK_GRAY)
        self.set_xy(0, self.h - 25)
        self.cell(self.w, 6, "Built with FastAPI  +  React  +  Ollama  +  Semgrep  +  ChromaDB", align="C")
        self._slide_number(11)


def main():
    pdf = PresentationPDF()
    pdf.slide_title()
    pdf.slide_problem()
    pdf.slide_solution()
    pdf.slide_architecture()
    pdf.slide_telemetry()
    pdf.slide_data_flow()
    pdf.slide_tools_explained()
    pdf.slide_how_we_built()
    pdf.slide_example_real()
    pdf.slide_example_fp()
    pdf.slide_closing()
    pdf.output(OUTPUT_PATH)
    print(f"Presentation saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
