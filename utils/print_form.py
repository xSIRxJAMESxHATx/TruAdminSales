"""
Generate a blank, print-ready PDF of the Exception Sales Intake form
so a rep can fill it out by hand when needed.
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


GREEN = HexColor("#2e7d32")
LIGHT_GREEN = HexColor("#e8f5e9")
MED_GREEN = HexColor("#81c784")
GRAY = HexColor("#616161")
LINE = HexColor("#a5d6a7")


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="FormTitle", fontName="Helvetica-Bold", fontSize=16,
        textColor=GREEN, alignment=TA_CENTER, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="FormSub", fontName="Helvetica", fontSize=9,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="Section", fontName="Helvetica-Bold", fontSize=11,
        textColor=GREEN, spaceBefore=10, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="Field", fontName="Helvetica", fontSize=9,
        textColor=black, leading=12
    ))
    styles.add(ParagraphStyle(
        name="Tiny", fontName="Helvetica", fontSize=7.5,
        textColor=GRAY, alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        name="Warn", fontName="Helvetica-Oblique", fontSize=8,
        textColor=HexColor("#c62828"), alignment=TA_CENTER, spaceBefore=6
    ))
    return styles


def _line_field(label: str, width_chars: int = 40) -> str:
    return f"<b>{label}</b> " + "_" * width_chars


def build_blank_form_pdf() -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
        topMargin=0.4 * inch, bottomMargin=0.4 * inch
    )
    s = _styles()
    story = []

    # Header
    story.append(Paragraph("🌿 LAWN CARE — SYSTEM EXCEPTION SALES INTAKE", s["FormTitle"]))
    story.append(Paragraph(
        "Blank form for handwritten entry when digital entry is unavailable. "
        "Return completed form to your processor / admin team.",
        s["FormSub"]
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=6))

    # ① Customer
    story.append(Paragraph("① CUSTOMER INFORMATION", s["Section"]))
    cust_data = [
        [Paragraph(_line_field("First Name", 28), s["Field"]),
         Paragraph(_line_field("Last Name", 28), s["Field"])],
        [Paragraph(_line_field("Phone", 28), s["Field"]),
         Paragraph(_line_field("Mobile / Alt", 28), s["Field"])],
        [Paragraph(_line_field("Email", 55), s["Field"]), ""],
        [Paragraph(_line_field("Street Address", 55), s["Field"]), ""],
        [Paragraph(_line_field("City", 22), s["Field"]),
         Paragraph(_line_field("State __", 8) + "  " + _line_field("ZIP", 12), s["Field"])],
        [Paragraph(_line_field("Property Sq Ft", 18), s["Field"]),
         Paragraph(_line_field("Grass Type", 28), s["Field"])],
    ]
    t = Table(cust_data, colWidths=[3.6 * inch, 3.6 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN),
        ("BOX", (0, 0), (-1, -1), 0.5, MED_GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("SPAN", (0, 2), (1, 2)),
        ("SPAN", (0, 3), (1, 3)),
    ]))
    story.append(t)

    story.append(Paragraph(
        "Areas serviced:  ☐ Front   ☐ Back   ☐ Right   ☐ Left"
        " &nbsp;&nbsp;&nbsp; Special:  ☐ Locked Gate  ☐ Pet  ☐ Invisible Fence  ☐ Sprinkler",
        s["Field"]
    ))
    story.append(Spacer(1, 4))

    # ② Services
    story.append(Paragraph("② SERVICES", s["Section"]))
    story.append(Paragraph(
        "Main Lawn / Expanded / Tree &amp; Shrub — one row per service. "
        "For Tree &amp; Shrub, mark rounds 1–8 (Y/N pattern).",
        s["Tiny"]
    ))

    hdr = [
        Paragraph("<b>Service Name</b>", s["Field"]),
        Paragraph("<b># Apps</b>", s["Field"]),
        Paragraph("<b>$ / App</b>", s["Field"]),
        Paragraph("<b>Discounts</b>", s["Field"]),
        Paragraph("<b>Pattern (T&amp;S)</b>", s["Field"]),
        Paragraph("<b>Line Total</b>", s["Field"]),
    ]
    blank_row = [
        Paragraph("_" * 22, s["Field"]),
        Paragraph("____", s["Field"]),
        Paragraph("______", s["Field"]),
        Paragraph("_" * 14, s["Field"]),
        Paragraph("1 2 3 4 5 6 7 8", s["Field"]),
        Paragraph("________", s["Field"]),
    ]
    svc_data = [hdr] + [blank_row[:] for _ in range(5)]
    st = Table(svc_data, colWidths=[2.0*inch, 0.7*inch, 0.8*inch, 1.4*inch, 1.4*inch, 0.9*inch])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GREEN),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("BACKGROUND", (0, 1), (-1, -1), white),
        ("BOX", (0, 0), (-1, -1), 0.5, MED_GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(st)
    story.append(Paragraph(
        "Discount codes (circle): 20% all · 50% 1st · 50% last · Last free · Military · Senior · Price match · Other $_____",
        s["Tiny"]
    ))
    story.append(Spacer(1, 4))

    # Totals box
    tot = [
        [Paragraph("<b>Subtotal $________</b>", s["Field"]),
         Paragraph("<b>Total Discount $________</b>", s["Field"]),
         Paragraph("<b>Sales Tax $________</b>", s["Field"]),
         Paragraph("<b>GRAND TOTAL $________</b>", s["Field"])],
    ]
    tt = Table(tot, colWidths=[1.8*inch, 1.9*inch, 1.7*inch, 1.8*inch])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN),
        ("BOX", (0, 0), (-1, -1), 1, GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, MED_GREEN),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(tt)

    # ③ Rep / Payment
    story.append(Paragraph("③ SALES REP · PAYMENT · REASON", s["Section"]))
    rep_data = [
        [Paragraph(_line_field("Employee ID", 16), s["Field"]),
         Paragraph(_line_field("Rep First", 16), s["Field"]),
         Paragraph(_line_field("Rep Last", 16), s["Field"])],
        [Paragraph(_line_field("Rep Email", 28), s["Field"]),
         Paragraph(_line_field("Business Unit", 18), s["Field"]),
         Paragraph(_line_field("Region", 16), s["Field"])],
        [Paragraph(_line_field("Sales Channel", 22), s["Field"]),
         Paragraph("Payment:  ☐ Prepay  ☐ Easypay  ☐ Invoice", s["Field"]),
         Paragraph("Prepay %:  ☐ 5  ☐ 7  ☐ 10", s["Field"])],
        [Paragraph(_line_field("Exception Reason", 55), s["Field"]), ""],
    ]
    rt = Table(rep_data, colWidths=[2.5*inch, 2.5*inch, 2.2*inch])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREEN),
        ("BOX", (0, 0), (-1, -1), 0.5, MED_GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("SPAN", (0, 3), (2, 3)),
    ]))
    story.append(rt)

    story.append(Paragraph("<b>Notes / Special Instructions</b> (do NOT write card numbers or sensitive payment data)", s["Field"]))
    notes_box = Table([[Paragraph("<br/><br/><br/><br/>", s["Field"])]], colWidths=[7.2*inch])
    notes_box.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, MED_GREEN),
        ("BACKGROUND", (0, 0), (-1, -1), white),
    ]))
    story.append(notes_box)

    story.append(Paragraph(
        "⚠️ Do not record credit-card numbers, bank accounts, SSNs, or other highly sensitive data on this form.",
        s["Warn"]
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=MED_GREEN, spaceAfter=4))
    story.append(Paragraph(
        "Rep signature: ___________________________  Date: ____________  "
        "Admin received: ___________________________  Date: ____________",
        s["Field"]
    ))
    story.append(Paragraph(
        "Lawn Care Exception Sales System · Printable blank intake form",
        s["Tiny"]
    ))

    doc.build(story)
    return buf.getvalue()
