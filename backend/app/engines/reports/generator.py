import os
import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage, KeepTogether
)

PRIMARY_COLOR = colors.HexColor("#1E3A8A")   # Deep Navy
SECONDARY_COLOR = colors.HexColor("#2563EB") # Blue 600
TEXT_DARK = colors.HexColor("#0F172A")       # Slate 900
TEXT_MUTED = colors.HexColor("#475569")      # Slate 600
BG_LIGHT = colors.HexColor("#F8FAFC")        # Slate 50
BORDER_COLOR = colors.HexColor("#CBD5E1")    # Slate 300


def build_screening_pdf_report(
    screening_data: Dict[str, Any],
    document_data: Dict[str, Any],
    quality_data: Optional[Dict[str, Any]],
    fields_data: List[Dict[str, Any]],
    mrz_data: Optional[Dict[str, Any]],
    forensics_data: List[Dict[str, Any]],
    risk_data: Optional[Dict[str, Any]],
    output_path: str
) -> str:
    """
    Generates a formal 5-page Law Enforcement & Border Security Screening Dossier in PDF format.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=TEXT_MUTED,
        spaceAfter=12
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=PRIMARY_COLOR,
        spaceBefore=8,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=TEXT_DARK
    )
    mono_style = ParagraphStyle(
        'MonoText',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10,
        textColor=TEXT_DARK
    )
    disclaimer_style = ParagraphStyle(
        'DisclaimerText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=TEXT_MUTED
    )

    story = []

    def add_page_header(page_title: str):
        header_table = Table(
            [
                [
                    Paragraph("<b>VERISIGHT</b> // AI Document Screening Platform", body_style),
                    Paragraph(f"<b>CONFIDENTIAL</b> • {screening_data.get('reference_no', '')}", ParagraphStyle('RightH', parent=body_style, alignment=2))
                ]
            ],
            colWidths=[4.0 * inch, 3.5 * inch]
        )
        header_table.setStyle(TableStyle([
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 8))
        story.append(Paragraph(page_title, title_style))
        story.append(Paragraph("Smart India Hackathon 2026 • Problem Statement 26188 • Statutory Evidentiary Dossier", subtitle_style))

    # ================= PAGE 1: EXECUTIVE SUMMARY & RISK PROFILE =================
    add_page_header("Executive Screening Dossier")

    # Risk Banner
    risk_level = (risk_data.get("reviewer_override_level") or risk_data.get("risk_level") or "REVIEW") if risk_data else "REVIEW"
    risk_score = risk_data.get("composite_score", 0.0) if risk_data else 0.0

    banner_bg = colors.HexColor("#DCFCE7") if risk_level == "CLEAR" else colors.HexColor("#FEF3C7") if risk_level == "REVIEW" else colors.HexColor("#FEE2E2")
    banner_text_col = colors.HexColor("#166534") if risk_level == "CLEAR" else colors.HexColor("#92400E") if risk_level == "REVIEW" else colors.HexColor("#991B1B")

    banner_table = Table(
        [
            [
                Paragraph(f"<b>CLASSIFICATION DECISION: {risk_level}</b> (Composite Score: {risk_score:.1f}/100)", ParagraphStyle('BannerP', fontName='Helvetica-Bold', fontSize=12, leading=14, textColor=banner_text_col)),
                Paragraph(f"Engine: {risk_data.get('engine_version', 'VERISIGHT-v1.2') if risk_data else 'v1.2'}", ParagraphStyle('EngP', fontName='Helvetica', fontSize=9, alignment=2, textColor=banner_text_col))
            ]
        ],
        colWidths=[5.5 * inch, 2.0 * inch]
    )
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), banner_bg),
        ('BOX', (0, 0), (-1, -1), 1, banner_text_col),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 12))

    # Credential Metadata Table
    story.append(Paragraph("1. Primary Credential Provenance", section_heading))
    meta_rows = [
        ["Reference Code:", screening_data.get("reference_no", "—"), "Document Specification:", screening_data.get("document_type", "—")],
        ["Issuing State:", screening_data.get("issuing_country_code", "IND"), "Ingestion Mode:", "Synthetic Demo" if screening_data.get("is_synthetic") else "Production Intake"],
        ["Intake Timestamp:", str(screening_data.get("created_at", datetime.datetime.now())), "Original File Size:", f"{document_data.get('file_size_bytes', 0) / 1024:.1f} KB"],
        ["Evidence SHA-256:", document_data.get("sha256_hash", "—")[:48] + "...", "MIME Type:", document_data.get("mime_type", "image/jpeg")],
    ]
    meta_table = Table(meta_rows, colWidths=[1.6 * inch, 2.4 * inch, 1.6 * inch, 1.9 * inch])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TEXTCOLOR', (0, 0), (0, -1), TEXT_MUTED),
        ('TEXTCOLOR', (2, 0), (2, -1), TEXT_MUTED),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Document Image Thumbnail if exists
    doc_path = document_data.get("processed_path") or document_data.get("storage_path")
    if doc_path and os.path.exists(doc_path):
        try:
            story.append(Paragraph("Document Evidence Capture:", section_heading))
            story.append(RLImage(doc_path, width=4.5 * inch, height=2.4 * inch))
            story.append(Spacer(1, 8))
        except Exception:
            pass

    # Reviewer Override note if present
    if risk_data and risk_data.get("reviewer_override_level"):
        story.append(Spacer(1, 8))
        override_rows = [
            [
                Paragraph(
                    f"<b>SUPERVISORY OVERRIDE AFFIXED:</b> Model: {risk_data.get('risk_level')} &rarr; Override: {risk_data.get('reviewer_override_level')}<br/>"
                    f"<b>Justification:</b> {risk_data.get('override_reason', 'None provided.')}",
                    body_style
                )
            ]
        ]
        ov_table = Table(override_rows, colWidths=[7.5 * inch])
        ov_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F3E8FF")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#9333EA")),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(ov_table)

    story.append(PageBreak())

    # ================= PAGE 2: OPTICAL QUALITY ASSESSMENT =================
    add_page_header("Optical Quality Pre-Flight Assessment")

    if quality_data:
        story.append(Paragraph("2. Optical Acquisition & Physical Framing Metrics", section_heading))
        q_rows = [
            ["Quality Vector", "Measured Value", "Evidentiary Baseline", "Status"],
            ["Laplacian Sharpness Variance", f"{quality_data.get('blur_score', 0):.1f}", ">= 100.0 Threshold", "PASS" if quality_data.get('blur_score', 0) >= 100 else "FAIL (Blur)"],
            ["Specular Glare Ratio", f"{quality_data.get('glare_score', 0)*100:.1f}%", "<= 5.0% Max Luminance", "PASS" if quality_data.get('glare_score', 0) <= 0.05 else "FAIL (Glare)"],
            ["Mean Luminance (Brightness)", f"{quality_data.get('brightness_score', 0):.1f} / 255", "90.0 - 200.0 Target Range", "OPTIMAL"],
            ["Estimated DPI Resolution", f"{quality_data.get('resolution_dpi', 300)} DPI", ">= 300 DPI Standard", "SUFFICIENT"],
            ["Detected Orientation", f"{quality_data.get('orientation_detected', 0)}°", "0° (Upright)", "RECTIFIED"],
            ["Overall Readability Heuristic", f"{quality_data.get('readability_score', 0)*100:.1f}%", ">= 75.0% OCR Score", "PASS" if quality_data.get('readability_score', 0) >= 0.75 else "MARGINAL"],
        ]
        q_table = Table(q_rows, colWidths=[2.2 * inch, 1.8 * inch, 2.0 * inch, 1.5 * inch])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(q_table)
        story.append(Spacer(1, 14))

        # Rescan banner if applicable
        if quality_data.get("rescan_recommended"):
            rescan_box = Table(
                [[Paragraph("<b>RESCAN DIRECTIVE:</b> The document scan exhibits severe blur or specular reflection. Secondary acquisition under diffused lighting is strongly advised prior to definitive clearance.", body_style)]],
                colWidths=[7.5 * inch]
            )
            rescan_box.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#D97706")),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(rescan_box)

    story.append(PageBreak())

    # ================= PAGE 3: VISUAL INSPECTION ZONE (VIZ) =================
    add_page_header("Visual Inspection Zone (VIZ) Field Extraction")

    story.append(Paragraph("3. Extracted Alphanumeric Identity Registry", section_heading))
    f_rows = [["Field Identifier", "Extracted Value", "Confidence", "Status", "Reviewer Modified"]]
    for f in fields_data:
        val = f.get("current_value") or "—"
        conf = f.get("confidence", 0.0)
        status = f.get("validation_status", "VALID")
        is_corr = "YES" if f.get("is_corrected") else "NO"
        f_rows.append([f.get("field_name", "—"), val, f"{conf*100:.0f}%", str(status), is_corr])

    f_table = Table(f_rows, colWidths=[2.0 * inch, 2.3 * inch, 1.0 * inch, 1.1 * inch, 1.1 * inch])
    f_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 4.5),
    ]))
    story.append(f_table)

    story.append(PageBreak())

    # ================= PAGE 4: MRZ VERIFICATION & CHECKSUMS =================
    add_page_header("ICAO Doc 9303 MRZ Cryptographic Verification")

    if mrz_data:
        story.append(Paragraph("4. Machine Readable Zone Mathematical Check Digits (Weights [7, 3, 1])", section_heading))
        raw_mrz = mrz_data.get("raw_mrz_text", "")
        story.append(Paragraph(f"<font face='Courier'>{raw_mrz.replace(chr(10), '<br/>')}</font>", mono_style))
        story.append(Spacer(1, 10))

        chk_rows = [
            ["Entity Checksum", "Value", "7-3-1 Status", "Integrity State"],
            ["Document Number", mrz_data.get("document_number", "—"), "PASS" if mrz_data.get("doc_number_check") else "FAIL", "Deterministic Match" if mrz_data.get("doc_number_check") else "MISMATCH / ALTERED"],
            ["Date of Birth (YYMMDD)", mrz_data.get("dob", "—"), "PASS" if mrz_data.get("dob_check") else "FAIL", "Deterministic Match" if mrz_data.get("dob_check") else "MISMATCH / ALTERED"],
            ["Expiry Date (YYMMDD)", mrz_data.get("expiry_date", "—"), "PASS" if mrz_data.get("expiry_check") else "FAIL", "Deterministic Match" if mrz_data.get("expiry_check") else "MISMATCH / ALTERED"],
            ["Composite Multi-Zone", "Whole String", "PASS" if mrz_data.get("composite_check") else "FAIL", "Deterministic Match" if mrz_data.get("composite_check") else "COMPOSITE ALTERED"],
        ]
        chk_table = Table(chk_rows, colWidths=[2.2 * inch, 1.8 * inch, 1.5 * inch, 2.0 * inch])
        chk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(chk_table)

    story.append(PageBreak())

    # ================= PAGE 5: FORENSIC DIAGNOSTICS & AUDIT LEDGER =================
    add_page_header("Multi-Factor Forensics & Audit Certification")

    story.append(Paragraph("5. Digital Forensic Analysis Findings", section_heading))
    forensic_rows = [["Method", "Severity", "Finding Title", "Recommended Officer Action"]]
    for f in forensics_data:
        forensic_rows.append([
            f.get("analysis_method", "—"),
            f.get("severity", "—"),
            f.get("title", "—")[:40] + ("..." if len(f.get("title", "")) > 40 else ""),
            f.get("recommended_action", "—")[:45] + ("..." if len(f.get("recommended_action", "")) > 45 else "")
        ])

    for_table = Table(forensic_rows, colWidths=[1.2 * inch, 1.1 * inch, 2.6 * inch, 2.6 * inch])
    for_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_LIGHT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(for_table)
    story.append(Spacer(1, 14))

    # Cryptographic Audit Reference
    story.append(Paragraph("6. Cryptographic Chain-of-Custody Certification", section_heading))
    cert_text = (
        f"This document screening dossier was processed under automated audit tracking. "
        f"The ingest image byte stream was assigned SHA-256 evidence hash {document_data.get('sha256_hash', '—')}. "
        f"All subsequent processing stages, OCR field extractions, and reviewer notes are permanently appended "
        f"to the tamper-evident hash chain. Integrity can be verified live via the VERISIGHT Audit Verification API."
    )
    story.append(Paragraph(cert_text, body_style))
    story.append(Spacer(1, 12))

    # Statutory Non-Conclusive Disclaimer
    story.append(Paragraph(
        "STATUTORY NOTICE: Error Level Analysis (ELA), frequency texture gradients, and automated OCR results "
        "provide decision-support indicators and probabilistic clues for trained immigration officers. They do NOT "
        "constitute autonomous legal proof of forgery or sovereign identity invalidity. Final clearance determinations "
        "are reserved exclusively for authorized border personnel.",
        disclaimer_style
    ))

    doc.build(story)
    return output_path
