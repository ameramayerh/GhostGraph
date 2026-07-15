import io
import xml.sax.saxutils as saxutils
from dataclasses import dataclass
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import CondPageBreak, SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


@dataclass(frozen=True)
class AttackContext:
    attack_type: str
    scenario: str
    impact: str
    remediation: str


DEPENDENCY_ATTACK_CONTEXT = AttackContext(
    "Known Vulnerable Component",
    "An attacker may target the publicly documented weakness when the affected package version and vulnerable functionality are reachable in this application.",
    "Impact depends on the advisory and how the package is used; it can range from service disruption or data exposure to code execution.",
    "Confirm the installed and runtime versions, review the linked advisory, upgrade to a patched compatible version, and retest the affected feature.",
)


ATTACK_CONTEXTS = (
    (
        ("unsafe-innerhtml", "innerhtml", "cross-site scripting", "xss"),
        AttackContext(
            "Cross-Site Scripting (XSS)",
            "If attacker-controlled text reaches this HTML-writing operation without sanitization, a crafted value could run active content in another user's browser session.",
            "This could expose page data, perform actions as the signed-in user, or alter what the victim sees.",
            "Use textContent for plain text. If HTML is required, allow only trusted markup and sanitize it with a maintained library.",
        ),
    ),
    (
        ("child-process-exec", "command injection", "shell command", "child_process"),
        AttackContext(
            "Operating-System Command Injection",
            "If untrusted input becomes part of the shell command, an attacker could change the intended command and make the server execute unintended operating-system actions.",
            "Successful abuse could read or modify files, expose secrets, or take control of the application process under its current permissions.",
            "Avoid a shell where possible. Use execFile or spawn with a fixed executable, separate arguments, strict allow-list validation, and least-privilege service permissions.",
        ),
    ),
    (
        ("javascript.eval", " eval", "code injection", "dynamic code"),
        AttackContext(
            "JavaScript Code Injection",
            "If a user can influence the string passed to eval, the application may treat that input as trusted JavaScript and execute it.",
            "The result could be unauthorized application behavior, access to in-process data, or further compromise depending on where the code runs.",
            "Remove eval and replace it with explicit parsing or a fixed mapping of allowed operations. Validate all external input.",
        ),
    ),
    (
        ("hardcoded-secret", "hardcoded secret", "hardcoded credential", "credential is hardcoded"),
        AttackContext(
            "Credential or Secret Exposure",
            "Anyone who can read the source code, repository history, build output, or leaked archive may recover the embedded secret and try to use it as the application or service account.",
            "A valid exposed credential could permit unauthorized API access, data disclosure, or actions billed or attributed to the project owner.",
            "Remove the secret from code, rotate it, store the replacement in protected environment configuration or a secret manager, and restrict its permissions.",
        ),
    ),
    (
        ("npm-audit", "software composition analysis", "vulnerable dependency", "known cve"),
        DEPENDENCY_ATTACK_CONTEXT,
    ),
    (
        ("sql injection", "sqli", "unsafe sql"),
        AttackContext(
            "SQL Injection",
            "If external input is joined directly into a database query, a crafted value could change the query's meaning instead of being handled only as data.",
            "This may allow unauthorized reading or modification of database records and, in severe cases, broader database compromise.",
            "Use parameterized queries or a safe ORM interface, validate expected input types, and give the database account only the permissions it needs.",
        ),
    ),
    (
        ("idor", "insecure direct object", "object ownership"),
        AttackContext(
            "Broken Access Control (IDOR)",
            "If the server trusts an object identifier without checking ownership or permission, a signed-in user could request another user's record by changing that identifier.",
            "This could disclose or modify another user's data and violate authorization boundaries.",
            "Perform server-side authorization for every requested object using the authenticated user's identity and deny access by default.",
        ),
    ),
    (
        ("path traversal", "directory traversal", "zip slip"),
        AttackContext(
            "Path Traversal",
            "If an external filename is resolved outside the intended directory, a crafted path could make the application read or overwrite files elsewhere on the system.",
            "This could expose configuration and secrets or modify application and operating-system files available to the process.",
            "Resolve paths to canonical form, require them to remain under an allowed base directory, reject traversal sequences, and use least-privilege filesystem access.",
        ),
    ),
    (
        ("ssrf", "server-side request forgery"),
        AttackContext(
            "Server-Side Request Forgery (SSRF)",
            "If the server fetches a user-selected address, an attacker could make it contact internal or otherwise restricted network services.",
            "This may expose internal data, cloud metadata, or services that are not directly reachable from outside.",
            "Allow-list required destinations and protocols, block private and metadata address ranges, validate redirects, and apply network egress controls.",
        ),
    ),
    (
        ("authentication", "authorization", "jwt", "password reset", "auth bypass"),
        AttackContext(
            "Authentication or Authorization Bypass",
            "If the suspected control is missing or can be bypassed, an attacker may reach a protected action without the identity or permission the application expects.",
            "This could permit account takeover, unauthorized data access, or use of privileged functions.",
            "Enforce authentication and role or ownership checks on the server, use established token libraries, and add negative authorization tests.",
        ),
    ),
    (
        ("business logic", "coupon", "payment", "quantity", "workflow"),
        AttackContext(
            "Business-Logic Abuse",
            "An attacker may submit valid-looking requests in an unexpected order or with manipulated values to bypass a rule the user interface normally enforces.",
            "Possible effects include incorrect prices, repeated rewards, invalid state changes, or financial and inventory errors.",
            "Revalidate business rules and state transitions on the server, reject impossible values, make sensitive actions idempotent, and add abuse-case tests.",
        ),
    ),
)


DEFAULT_ATTACK_CONTEXT = AttackContext(
    "Application Security Weakness",
    "If untrusted input can reach this code in the required state, an attacker may be able to influence behavior beyond what the application intended. A reviewer must confirm the input path and security controls.",
    "The exact impact depends on reachability, existing protections, and the privileges of the affected component.",
    "Trace the data flow, validate input at the trust boundary, apply the relevant secure coding control, and add a regression test.",
)


def classify_attack(finding) -> AttackContext:
    """Map scanner evidence to a cautious, presentation-friendly attack scenario."""
    rule_id = str(getattr(finding, "semgrep_rule_id", "") or "").lower()
    if rule_id == "npm-audit-cve":
        # The advisory can contain terms such as XSS or command injection, but
        # package reachability and remediation differ from a direct code match.
        return DEPENDENCY_ATTACK_CONTEXT

    evidence = " ".join(
        str(value or "")
        for value in (
            getattr(finding, "semgrep_rule_id", ""),
            getattr(finding, "title", ""),
            getattr(finding, "description", ""),
            getattr(finding, "category", ""),
        )
    ).lower()
    for keywords, context in ATTACK_CONTEXTS:
        if any(keyword in evidence for keyword in keywords):
            return context
    return DEFAULT_ATTACK_CONTEXT


def safe_paragraph_text(value: str | None) -> str:
    return saxutils.escape(value or "Not available.").replace("\n", "<br/>")


def draw_page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#e2e8f0'))
    canvas.line(doc.leftMargin, 38, letter[0] - doc.rightMargin, 38)
    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(colors.HexColor('#64748b'))
    canvas.drawString(doc.leftMargin, 26, "GhostGraph | Authorized source-code security review")
    canvas.drawRightString(letter[0] - doc.rightMargin, 26, f"Page {doc.page}")
    canvas.restoreState()


def generate_pdf_report(engagement, findings, audit_logs) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    h2_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Custom styles
    finding_title_style = ParagraphStyle(
        'FindingTitle',
        parent=styles['Heading3'],
        textColor=colors.HexColor('#1f2937')
    )
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=8,
        textColor=colors.HexColor('#2563eb'),
        backColor=colors.HexColor('#f1f5f9'),
        borderPadding=5
    )
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['BodyText'],
        fontSize=7,
        leading=9,
    )
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=table_cell_style,
        fontName='Helvetica-Bold',
    )
    
    # Title
    title_text = Paragraph("<b><font size='24' color='#1e3a8a'>GhostGraph</font></b><br/><font size='16' color='#475569'>Source-Code Security Report</font>", title_style)
    elements.append(title_text)
    elements.append(Spacer(1, 24))
    
    # Engagement Info
    info_data = [
        ["Project Name:", engagement.name, "Date:", datetime.now().strftime('%Y-%m-%d')],
        ["Scope:", engagement.scope, "Authorized By:", engagement.authorized_by],
        ["Total Findings:", str(engagement.total_findings), "AI Review Progress:", str(engagement.filtered_findings)]
    ]
    info_table = Table(info_data, colWidths=[100, 150, 100, 150])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#334155')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0'))
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 30))

    # Table of Contents
    elements.append(Paragraph("Table of Contents", h2_style))
    toc_text = """
    1. Introduction & Methodology<br/>
    2. Executive Findings Summary<br/>
    3. Vulnerability Catalogue<br/>
    4. Detailed Finding Explanations & Remediation<br/>
    """
    elements.append(Paragraph(toc_text, normal_style))
    elements.append(Spacer(1, 30))

    # Methodology / Explanation
    elements.append(Paragraph("How We Found These Vulnerabilities", h2_style))
    methodology_text = """
    GhostGraph combines rule-based scanning, dependency auditing, and optional AI-assisted review:
    <br/><br/>
    <b>1. Software Composition Analysis (SCA):</b> We scan your project dependencies (like npm packages) for known CVEs and vulnerable versions.
    <br/>
    <b>2. Static Application Security Testing (SAST):</b> Semgrep evaluates source code against the bundled GhostGraph rules and records matching files and line numbers.
    <br/>
    <b>3. Optional AI-assisted review:</b> When a supported model is configured, selected security-sensitive files can be reviewed for potential authorization, authentication, and business-logic risks.
    <br/><br/>
    AI-generated results are advisory and require human verification. Rule-based findings remain available when no AI provider is configured.
    """
    elements.append(Paragraph(methodology_text, normal_style))
    elements.append(Spacer(1, 30))
    
    # Findings Summary Table
    elements.append(Paragraph("Findings Summary", h2_style))
    
    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for f in findings:
        if f.severity in severity_counts:
            severity_counts[f.severity] += 1
            
    summary_data = [
        ["Severity", "Count"],
        ["Critical", severity_counts["Critical"]],
        ["High", severity_counts["High"]],
        ["Medium", severity_counts["Medium"]],
        ["Low", severity_counts["Low"]]
    ]
    
    t = Table(summary_data, colWidths=[200, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 30))
    
    # Catalogue / Table of Contents
    elements.append(Paragraph("Vulnerability Catalogue", h2_style))
    if not findings:
        elements.append(Paragraph("No vulnerabilities found.", normal_style))
    else:
        catalog_data = [[
            Paragraph("#", table_header_style),
            Paragraph("Severity", table_header_style),
            Paragraph("Attack Type", table_header_style),
            Paragraph("Title", table_header_style),
            Paragraph("File", table_header_style),
        ]]
        for idx, f in enumerate(findings, 1):
            file_short = f.file_path.split('/')[-1] if '/' in f.file_path else f.file_path.split('\\')[-1]
            attack = classify_attack(f)
            catalog_data.append([
                Paragraph(str(idx), table_cell_style),
                Paragraph(saxutils.escape(f.severity), table_cell_style),
                Paragraph(saxutils.escape(attack.attack_type), table_cell_style),
                Paragraph(saxutils.escape(f.title), table_cell_style),
                Paragraph(saxutils.escape(file_short), table_cell_style),
            ])
            
        cat_table = Table(catalog_data, colWidths=[25, 55, 120, 145, 105])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        elements.append(cat_table)
    
    elements.append(Spacer(1, 30))
    
    # Findings Details
    elements.append(Paragraph("Detailed Findings", h2_style))
    if not findings:
        elements.append(Paragraph("No vulnerabilities found during this scan.", normal_style))
    
    for idx, f in enumerate(findings, 1):
        # Avoid leaving a finding title at the bottom with its explanation on the
        # next page. Large findings may still split naturally after this minimum.
        elements.append(CondPageBreak(240))
        # Severity color block
        sev_color = colors.red if f.severity in ['High', 'Critical'] else colors.orange if f.severity == 'Medium' else colors.blue
        attack = classify_attack(f)

        safe_title = saxutils.escape(f.title)
        safe_category = saxutils.escape(f.category)
        safe_path = saxutils.escape(f.file_path)
        elements.append(Paragraph(f"<font color='{sev_color.hexval()}'>[{f.severity}]</font> <b>#{idx} - {safe_title}</b>", finding_title_style))
        elements.append(Paragraph(f"<b>Category:</b> {safe_category}  |  <b>Location:</b> {safe_path}:{f.line_number}", normal_style))
        elements.append(Paragraph(f"<b>Attack Type:</b> {saxutils.escape(attack.attack_type)}", normal_style))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph(f"<b>Description:</b>", normal_style))
        elements.append(Paragraph(safe_paragraph_text(f.description), normal_style))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>How This Might Be Used by an Attacker:</b>", normal_style))
        elements.append(Paragraph(safe_paragraph_text(attack.scenario), normal_style))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Likely Impact:</b>", normal_style))
        elements.append(Paragraph(safe_paragraph_text(f.business_impact or attack.impact), normal_style))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Recommended Defense:</b>", normal_style))
        elements.append(Paragraph(safe_paragraph_text(f.remediation or attack.remediation), normal_style))
        elements.append(Spacer(1, 6))

        review_status = "Likely false positive" if f.is_false_positive else f.filtering_status
        elements.append(Paragraph(
            f"<b>Review Status:</b> {saxutils.escape(review_status)}. "
            "The scenario describes plausible risk; it is not proof that exploitation succeeded.",
            normal_style,
        ))
        elements.append(Spacer(1, 6))
        
        if f.code_snippet:
            elements.append(Paragraph(f"<b>Code Snippet:</b>", normal_style))
            elements.append(Spacer(1, 3))
            safe_code = saxutils.escape(f.code_snippet)
            elements.append(Paragraph(safe_code, code_style))
            elements.append(Spacer(1, 6))
            
        if f.ai_explanation:
            elements.append(Paragraph(f"<b>AI Explanation:</b>", normal_style))
            elements.append(Paragraph(safe_paragraph_text(f.ai_explanation), normal_style))
            
            if f.code_patch:
                elements.append(Spacer(1, 6))
                safe_patch = saxutils.escape(f.code_patch)
                elements.append(Paragraph(f"<b>Suggested Patch:</b>", normal_style))
                elements.append(Paragraph(safe_patch, code_style))
                
        elements.append(Spacer(1, 18))
        
    doc.build(elements, onFirstPage=draw_page_footer, onLaterPages=draw_page_footer)
    buffer.seek(0)
    return buffer
