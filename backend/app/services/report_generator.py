import io
import xml.sax.saxutils as saxutils
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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
    
    # Title
    title_text = Paragraph("<b><font size='24' color='#1e3a8a'>GhostGraph</font></b><br/><font size='16' color='#475569'>Advanced Security Report</font>", title_style)
    elements.append(title_text)
    elements.append(Spacer(1, 24))
    
    # Engagement Info
    info_data = [
        ["Project Name:", engagement.name, "Date:", datetime.now().strftime('%Y-%m-%d')],
        ["Scope:", engagement.scope, "Authorized By:", engagement.authorized_by],
        ["Total Findings:", str(engagement.total_findings), "AI Filtered:", str(engagement.filtered_findings)]
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
    GhostGraph uses a state-of-the-art Hybrid Analysis Engine to detect security flaws. We combine three distinct approaches:
    <br/><br/>
    <b>1. Software Composition Analysis (SCA):</b> We scan your project dependencies (like npm packages) for known CVEs and vulnerable versions.
    <br/>
    <b>2. Static Application Security Testing (SAST):</b> We use Semgrep to analyze your raw source code against thousands of known dangerous patterns (e.g., SQL Injection, XSS).
    <br/>
    <b>3. Agentic Threat Hunter (AI):</b> We use a Large Language Model to act as a virtual penetration tester, deeply reading your routing and controller files to find complex Business Logic Flaws, IDORs, and Authentication Bypasses that static analysis cannot see.
    <br/><br/>
    Finally, our AI Pre-Filtering Engine performs Reachability Analysis to remove false positives and test data from the final report.
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
        catalog_data = [["#", "Severity", "Title", "File"]]
        for idx, f in enumerate(findings, 1):
            file_short = f.file_path.split('/')[-1] if '/' in f.file_path else f.file_path.split('\\')[-1]
            catalog_data.append([str(idx), f.severity, f.title[:40] + ("..." if len(f.title) > 40 else ""), file_short])
            
        cat_table = Table(catalog_data, colWidths=[30, 70, 250, 150])
        cat_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        elements.append(cat_table)
    
    elements.append(Spacer(1, 30))
    
    # Findings Details
    elements.append(Paragraph("Detailed Findings", h2_style))
    if not findings:
        elements.append(Paragraph("No vulnerabilities found during this scan.", normal_style))
    
    for idx, f in enumerate(findings, 1):
        # Severity color block
        sev_color = colors.red if f.severity in ['High', 'Critical'] else colors.orange if f.severity == 'Medium' else colors.blue
        
        elements.append(Paragraph(f"<font color='{sev_color.hexval()}'>[{f.severity}]</font> <b>#{idx} - {f.title}</b>", finding_title_style))
        elements.append(Paragraph(f"<b>Category:</b> {f.category}  |  <b>Location:</b> {f.file_path}:{f.line_number}", normal_style))
        elements.append(Spacer(1, 8))
        
        elements.append(Paragraph(f"<b>Description:</b>", normal_style))
        safe_desc = saxutils.escape(f.description) if f.description else ""
        elements.append(Paragraph(safe_desc, normal_style))
        elements.append(Spacer(1, 6))
        
        if f.code_snippet:
            elements.append(Paragraph(f"<b>Code Snippet:</b>", normal_style))
            safe_code = saxutils.escape(f.code_snippet)
            elements.append(Paragraph(safe_code, code_style))
            elements.append(Spacer(1, 6))
            
        if f.ai_explanation:
            elements.append(Paragraph(f"<b>AI Explanation:</b>", normal_style))
            safe_ai = saxutils.escape(f.ai_explanation)
            elements.append(Paragraph(safe_ai, normal_style))
            elements.append(Spacer(1, 6))
            
            elements.append(Paragraph(f"<b>Business Impact:</b>", normal_style))
            safe_impact = saxutils.escape(f.business_impact) if f.business_impact else ""
            elements.append(Paragraph(safe_impact, normal_style))
            elements.append(Spacer(1, 6))
            
            elements.append(Paragraph(f"<b>Secure Refactoring:</b>", normal_style))
            safe_rem = saxutils.escape(f.remediation) if f.remediation else ""
            elements.append(Paragraph(safe_rem, normal_style))
            
            if f.code_patch:
                elements.append(Spacer(1, 6))
                safe_patch = saxutils.escape(f.code_patch)
                elements.append(Paragraph(f"<b>Suggested Patch:</b>", normal_style))
                elements.append(Paragraph(safe_patch, code_style))
                
        elements.append(Spacer(1, 18))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer
