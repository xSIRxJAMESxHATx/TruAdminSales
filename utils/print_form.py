"""
Polished, compact blank Exception Sales Intake PDF for handwritten use.
Totals row is compact so all calculations remain visible on one page.
"""
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


GREEN = HexColor("#1b5e20")
LIGHT = HexColor("#f1f8e9")
MED = HexColor("#81c784")
GRAY = HexColor("#546e7a")
LINE = HexColor("#a5d6a7")
HEADER_BG = HexColor("#2e7d32")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="FormTitle", fontName="Helvetica-Bold", fontSize=13,
        textColor=GREEN, alignment=TA_CENTER, spaceAfter=2, leading=15
    ))
    styles.add(ParagraphStyle(
        name="FormSub", fontName="Helvetica", fontSize=7.5,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=4, leading=9
    ))
    styles.add(ParagraphStyle(
        name="Section", fontName="Helvetica-Bold", fontSize=9,
        textColor=white, alignment=TA_LEFT, leading=11
    ))
    styles.add(ParagraphStyle(
        name="Field", fontName="Helvetica", fontSize=8,
        textColor=black, leading=10
    ))
    styles.add(ParagraphStyle(
        name="FieldSm", fontName="Helvetica", fontSize=7.5,
        textColor=black, leading=9
    ))
    styles.add(ParagraphStyle(
        name="Tiny", fontName="Helvetica", fontSize=7,
        textColor=GRAY, alignment=TA_CENTER, leading=8
    ))
    styles.add(ParagraphStyle(
        name="Warn", fontName="Helvetica-Oblique", fontSize=7,
        textColor=HexColor("#c62828"), alignment=TA_CENTER, spaceBefore=3
    ))
    styles.add(ParagraphStyle(
        name="HdrWhite", fontName="Helvetica-Bold", fontSize=8,
        textColor=white, leading=10
    ))
    return styles


def _lf(label: str, n: int = 30) -> str:
    return f"<b>{label}</b> " + "_" * n


def build_blank_form_pdf() -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.45 * inch, rightMargin=0.45 * inch,
        topMargin=0.28 * inch, bottomMargin=0.28 * inch,
    )
    s = _styles()
    story = []

    # Header
    story.append(Paragraph("LAWN CARE — SYSTEM EXCEPTION SALES INTAKE", s["FormTitle"]))
    story.append(Paragraph(
        "Blank form for handwritten entry · Return to processing team · Do not write card numbers or sensitive payment data",
        s["FormSub"]
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=GREEN, spaceAfter=4))

    def section_bar(title: str):
        bar = Table(
            [[Paragraph(title, s["Section"])]],
            colWidths=[7.6 * inch]
        )
        bar.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HEADER_BG),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROUNDEDCORNERS", [3, 3, 3, 3]),
        ]))
        return bar

    # ① Customer
    story.append(section_bar("①  CUSTOMER INFORMATION"))
    story.append(Spacer(1, 3))
    cust = [
        [Paragraph(_lf("First Name", 26), s["Field"]),
         Paragraph(_lf("Last Name", 26), s["Field"]),
         Paragraph(_lf("Phone", 18), s["Field"])],
        [Paragraph(_lf("Mobile / Alt", 22), s["Field"]),
         Paragraph(_lf("Email", 40), s["Field"]), ""],
        [Paragraph(_lf("Street", 50), s["Field"]), "", ""],
        [Paragraph(_lf("City", 22), s["Field"]),
         Paragraph(_lf("State", 6), s["Field"]),
         Paragraph(_lf("ZIP", 12), s["Field"])],
        [Paragraph(_lf("Sq Ft", 12), s["Field"]),
         Paragraph(_lf("Grass Type", 20), s["Field"]),
         Paragraph("Areas: ☐F ☐B ☐R ☐L", s["FieldSm"])],
        [Paragraph("Special: ☐ Locked gate  ☐ Pet  ☐ Invisible fence  ☐ Sprinkler", s["FieldSm"]), "", ""],
    ]
    ct = Table(cust, colWidths=[2.7*inch, 2.7*inch, 2.2*inch])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.4, MED),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("SPAN", (1, 1), (2, 1)),
        ("SPAN", (0, 2), (2, 2)),
        ("SPAN", (0, 5), (2, 5)),
    ]))
    story.append(ct)
    story.append(Spacer(1, 5))

    # ② Services
    story.append(section_bar("②  SERVICES  (one row per service · Tree & Shrub: mark rounds 1–8)"))
    story.append(Spacer(1, 3))
    hdr = [Paragraph(h, s["HdrWhite"]) for h in
           ["Service Name", "#Apps", "$/App", "Discounts / codes", "T&S Pattern", "Line $"]]
    blank = [
        Paragraph("_" * 20, s["FieldSm"]),
        Paragraph("___", s["FieldSm"]),
        Paragraph("_____", s["FieldSm"]),
        Paragraph("_" * 16, s["FieldSm"]),
        Paragraph("☐1 ☐2 ☐3 ☐4 ☐5 ☐6 ☐7 ☐8", s["FieldSm"]),
        Paragraph("______", s["FieldSm"]),
    ]
    rows = [hdr] + [list(blank) for _ in range(4)]
    st = Table(rows, colWidths=[2.0*inch, 0.55*inch, 0.7*inch, 1.55*inch, 1.85*inch, 0.75*inch])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (-1, -1), white),
        ("BOX", (0, 0), (-1, -1), 0.4, MED),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(st)
    story.append(Paragraph(
        "Discount codes: 20% all · 50% 1st · 50% last · Last free · Military · Senior · Price match · Other $____",
        s["Tiny"]
    ))
    story.append(Spacer(1, 3))

    # Compact totals — single thin row
    tot_cells = [
        Paragraph("<b>Subtotal</b> $_______", s["FieldSm"]),
        Paragraph("<b>Discounts</b> $_______", s["FieldSm"]),
        Paragraph("<b>Tax</b> $_______", s["FieldSm"]),
        Paragraph("<b>Prepay %</b> ___", s["FieldSm"]),
        Paragraph("<b>GRAND TOTAL</b> $________", s["FieldSm"]),
    ]
    tt = Table([tot_cells], colWidths=[1.5*inch, 1.5*inch, 1.3*inch, 1.1*inch, 2.0*inch])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, MED),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (4, 0), (4, 0), HexColor("#c8e6c9")),
    ]))
    story.append(tt)
    story.append(Spacer(1, 5))

    # ③ Rep / payment
    story.append(section_bar("③  SALES REP · PAYMENT · EXCEPTION REASON"))
    story.append(Spacer(1, 3))
    rep = [
        [Paragraph(_lf("Emp ID", 12), s["Field"]),
         Paragraph(_lf("First", 14), s["Field"]),
         Paragraph(_lf("Last", 14), s["Field"]),
         Paragraph(_lf("Email", 22), s["Field"])],
        [Paragraph(_lf("Branch / BU", 18), s["Field"]),
         Paragraph(_lf("Region", 14), s["Field"]),
         Paragraph(_lf("Channel", 16), s["Field"]),
         Paragraph("Pay: ☐Prepay ☐Easy ☐Inv", s["FieldSm"])],
        [Paragraph("Prepay %: ☐5 ☐7 ☐10", s["FieldSm"]),
         Paragraph(_lf("Exception reason", 48), s["Field"]), "", ""],
    ]
    rt = Table(rep, colWidths=[1.9*inch, 1.9*inch, 1.9*inch, 1.9*inch])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.4, MED),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("SPAN", (1, 2), (3, 2)),
    ]))
    story.append(rt)
    story.append(Spacer(1, 3))

    story.append(Paragraph("<b>Notes / special instructions</b>", s["FieldSm"]))
    notes = Table([[Paragraph("<br/><br/>", s["Field"])]], colWidths=[7.6*inch])
    notes.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.4, MED),
        ("BACKGROUND", (0, 0), (-1, -1), white),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(notes)

    story.append(Paragraph(
        "Do not record credit-card numbers, bank accounts, SSNs, or other highly sensitive data on this form.",
        s["Warn"]
    ))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=0.8, color=MED, spaceAfter=3))
    story.append(Paragraph(
        "Rep signature: ________________________  Date: __________   "
        "Received by: ________________________  Date: __________",
        s["FieldSm"]
    ))
    story.append(Paragraph("Lawn Care Exception Sales · Printable intake form", s["Tiny"]))

    doc.build(story)
    return buf.getvalue()
