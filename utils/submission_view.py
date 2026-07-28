"""
Full read-only rendering of a submission + printable snapshot PDF.
"""
from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Dict, Optional

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
HEADER_BG = HexColor("#2e7d32")


def _s():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="T", fontName="Helvetica-Bold", fontSize=12,
                              textColor=GREEN, alignment=TA_CENTER, spaceAfter=2))
    styles.add(ParagraphStyle(name="Sub", fontName="Helvetica", fontSize=8,
                              textColor=GRAY, alignment=TA_CENTER, spaceAfter=4))
    styles.add(ParagraphStyle(name="Sec", fontName="Helvetica-Bold", fontSize=9,
                              textColor=white, leading=11))
    styles.add(ParagraphStyle(name="F", fontName="Helvetica", fontSize=8,
                              textColor=black, leading=10))
    styles.add(ParagraphStyle(name="Sm", fontName="Helvetica", fontSize=7.5,
                              textColor=black, leading=9))
    styles.add(ParagraphStyle(name="Tiny", fontName="Helvetica", fontSize=7,
                              textColor=GRAY, alignment=TA_CENTER))
    return styles


def _bar(title: str, s):
    t = Table([[Paragraph(title, s["Sec"])]], colWidths=[7.6 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HEADER_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def build_submission_snapshot_pdf(sub: Dict[str, Any]) -> bytes:
    """Read-only full image of the original sale submission."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.45 * inch, rightMargin=0.45 * inch,
        topMargin=0.3 * inch, bottomMargin=0.3 * inch,
    )
    s = _s()
    story = []
    sid = sub.get("id", "?")
    status = (sub.get("status") or "").upper()
    story.append(Paragraph(
        f"EXCEPTION SALE SUBMISSION  #{sid}  ·  {status}", s["T"]
    ))
    story.append(Paragraph(
        f"Submitted {(sub.get('created_at') or '')[:19].replace('T', ' ')} UTC  ·  "
        f"Updated {(sub.get('updated_at') or '')[:19].replace('T', ' ')}  ·  READ-ONLY SNAPSHOT",
        s["Sub"]
    ))
    story.append(HRFlowable(width="100%", thickness=1.2, color=GREEN, spaceAfter=4))

    # Customer
    story.append(_bar("①  CUSTOMER", s))
    story.append(Spacer(1, 3))
    areas = json.loads(sub.get("areas_serviced") or "[]")
    special = json.loads(sub.get("special_params") or "[]")
    cust = [
        [Paragraph(f"<b>Name</b>  {sub.get('cust_first','')} {sub.get('cust_last','')}", s["F"]),
         Paragraph(f"<b>Phone</b>  {sub.get('cust_phone','')}", s["F"]),
         Paragraph(f"<b>Mobile</b>  {sub.get('cust_mobile') or '—'}", s["F"])],
        [Paragraph(f"<b>Email</b>  {sub.get('cust_email') or '—'}", s["F"]),
         Paragraph(f"<b>Sq Ft</b>  {sub.get('property_sqft') or '—'}", s["F"]),
         Paragraph(f"<b>Grass</b>  {sub.get('grass_type') or '—'}", s["F"])],
        [Paragraph(
            f"<b>Address</b>  {sub.get('cust_street','')}, {sub.get('cust_city','')}, "
            f"{sub.get('cust_state','')} {sub.get('cust_zip','')}", s["F"]), "", ""],
        [Paragraph(f"<b>Areas</b>  {', '.join(areas) or '—'}", s["Sm"]),
         Paragraph(f"<b>Special</b>  {', '.join(special) or '—'}", s["Sm"]), ""],
    ]
    ct = Table(cust, colWidths=[2.7*inch, 2.5*inch, 2.4*inch])
    ct.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.4, MED),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, MED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("SPAN", (0, 2), (2, 2)),
        ("SPAN", (1, 3), (2, 3)),
    ]))
    story.append(ct)
    story.append(Spacer(1, 5))

    # Services
    story.append(_bar("②  SERVICES / PROGRAMS", s))
    story.append(Spacer(1, 3))
    try:
        services = json.loads(sub.get("services_json") or "[]")
    except Exception:
        services = []
    hdr = [Paragraph(h, ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=7.5, textColor=white))
           for h in ["Service / Program", "Type", "Apps", "$/App", "Pattern", "Base", "Disc", "Tax", "Line $"]]
    rows = [hdr]
    for svc in services:
        rows.append([
            Paragraph(str(svc.get("name") or "—"), s["Sm"]),
            Paragraph(str(svc.get("service_type") or "—"), s["Sm"]),
            Paragraph(str(svc.get("num_apps") or "—"), s["Sm"]),
            Paragraph(f"${float(svc.get('price') or 0):.2f}", s["Sm"]),
            Paragraph(str(svc.get("pattern") or "—"), s["Sm"]),
            Paragraph(f"${float(svc.get('line_base') or 0):.2f}", s["Sm"]),
            Paragraph(f"${float(svc.get('line_discount') or 0):.2f}", s["Sm"]),
            Paragraph(f"${float(svc.get('line_tax') or 0):.2f}", s["Sm"]),
            Paragraph(f"${float(svc.get('line_total') or 0):.2f}", s["Sm"]),
        ])
    if len(rows) == 1:
        rows.append([Paragraph("No services recorded", s["Sm"])] + [""] * 8)
    st = Table(rows, colWidths=[1.6*inch, 0.7*inch, 0.45*inch, 0.6*inch, 0.85*inch,
                                0.65*inch, 0.6*inch, 0.55*inch, 0.7*inch])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("BACKGROUND", (0, 1), (-1, -1), white),
        ("BOX", (0, 0), (-1, -1), 0.4, MED),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, MED),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(st)
    story.append(Spacer(1, 4))

    # Totals
    tot = [[
        Paragraph(f"<b>Subtotal</b>  ${float(sub.get('subtotal') or 0):.2f}", s["Sm"]),
        Paragraph(f"<b>Discount</b>  ${float(sub.get('total_discount') or 0):.2f}", s["Sm"]),
        Paragraph(f"<b>Tax</b>  ${float(sub.get('total_tax') or 0):.2f}", s["Sm"]),
        Paragraph(f"<b>Prepay</b>  {sub.get('prepay_pct') or 0}%", s["Sm"]),
        Paragraph(f"<b>GRAND TOTAL</b>  ${float(sub.get('grand_total') or 0):.2f}", s["F"]),
    ]]
    tt = Table(tot, colWidths=[1.5*inch, 1.5*inch, 1.3*inch, 1.2*inch, 2.1*inch])
    tt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, GREEN),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, MED),
        ("BACKGROUND", (4, 0), (4, 0), HexColor("#c8e6c9")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(tt)
    story.append(Spacer(1, 5))

    # Rep
    story.append(_bar("③  SALES REP · PAYMENT · REASON", s))
    story.append(Spacer(1, 3))
    rep = [
        [Paragraph(f"<b>Emp ID</b>  {sub.get('emp_id','')}", s["F"]),
         Paragraph(f"<b>Rep</b>  {sub.get('rep_first','')} {sub.get('rep_last','')}", s["F"]),
         Paragraph(f"<b>Email</b>  {sub.get('rep_email') or '—'}", s["F"])],
        [Paragraph(f"<b>BU</b>  {sub.get('business_unit') or '—'}", s["F"]),
         Paragraph(f"<b>Region</b>  {sub.get('region') or '—'}", s["F"]),
         Paragraph(f"<b>Channel</b>  {sub.get('sales_channel') or '—'}", s["F"])],
        [Paragraph(f"<b>Payment</b>  {sub.get('payment_type') or '—'}", s["F"]),
         Paragraph(f"<b>Exception</b>  {sub.get('exception_reason') or '—'}", s["F"]), ""],
    ]
    rt = Table(rep, colWidths=[2.5*inch, 2.6*inch, 2.5*inch])
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.4, MED),
        ("INNERGRID", (0, 0), (-1, -1), 0.2, MED),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("SPAN", (1, 2), (2, 2)),
    ]))
    story.append(rt)
    story.append(Spacer(1, 4))

    story.append(Paragraph(f"<b>Sales notes:</b>  {sub.get('sales_notes') or '—'}", s["F"]))
    story.append(Paragraph(
        f"<b>Processor:</b>  {sub.get('admin_user') or '—'}  ·  "
        f"<b>Admin notes:</b>  {sub.get('admin_notes') or '—'}  ·  "
        f"<b>Kick:</b>  {sub.get('kick_reason') or '—'}",
        s["F"]
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.6, color=MED, spaceAfter=3))
    story.append(Paragraph(
        "Lawn Care Exception Sales · Read-only original submission snapshot",
        s["Tiny"]
    ))
    doc.build(story)
    return buf.getvalue()


def render_submission_detail(sub: Dict[str, Any], *, show_pdf_button: bool = True):
    """Streamlit full detail panel for a submission record."""
    import streamlit as st

    status = sub.get("status") or ""
    st.markdown(
        f'<span class="badge-{status}">{status.upper()}</span>  '
        f'&nbsp; **#{sub.get("id")}**  ·  '
        f'Submitted `{(sub.get("created_at") or "")[:19]}`',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Customer")
        st.write(f"**{sub.get('cust_first')} {sub.get('cust_last')}**")
        st.write(f"📞 {sub.get('cust_phone')}  ·  {sub.get('cust_mobile') or '—'}")
        st.write(f"✉️ {sub.get('cust_email') or '—'}")
        st.write(
            f"📍 {sub.get('cust_street')}, {sub.get('cust_city')}, "
            f"{sub.get('cust_state')} {sub.get('cust_zip')}"
        )
        areas = json.loads(sub.get("areas_serviced") or "[]")
        special = json.loads(sub.get("special_params") or "[]")
        st.caption(
            f"Sq ft: {sub.get('property_sqft') or '—'} · Grass: {sub.get('grass_type') or '—'}  \n"
            f"Areas: {', '.join(areas) or '—'} · Special: {', '.join(special) or '—'}"
        )
    with c2:
        st.markdown("#### Rep & channel")
        st.write(f"**{sub.get('rep_first')} {sub.get('rep_last')}** ({sub.get('emp_id')})")
        st.write(f"Email: {sub.get('rep_email') or '—'}")
        st.write(f"BU: {sub.get('business_unit') or '—'} · Region: {sub.get('region') or '—'}")
        st.write(f"Channel: {sub.get('sales_channel') or '—'}")
        st.write(f"Payment: **{sub.get('payment_type')}** · Prepay {sub.get('prepay_pct') or 0}%")
        st.write(f"Exception: *{sub.get('exception_reason') or '—'}*")
    with c3:
        st.markdown("#### Totals")
        st.metric("Grand total", f"${float(sub.get('grand_total') or 0):.2f}")
        st.caption(
            f"Sub ${float(sub.get('subtotal') or 0):.2f} · "
            f"Disc ${float(sub.get('total_discount') or 0):.2f} · "
            f"Tax ${float(sub.get('total_tax') or 0):.2f}"
        )
        st.write(f"Processor: **{sub.get('admin_user') or '—'}**")
        if sub.get("kick_reason"):
            st.error(f"Kick: {sub['kick_reason']}")
        if sub.get("admin_notes"):
            st.info(f"Admin notes: {sub['admin_notes']}")
        if sub.get("sales_notes"):
            st.write(f"Sales notes: {sub['sales_notes']}")

    st.markdown("#### Services / programs")
    try:
        services = json.loads(sub.get("services_json") or "[]")
    except Exception:
        services = []
    if services:
        for svc in services:
            discs = svc.get("disc_labels") or [
                d.get("label") for d in (svc.get("discounts") or []) if d.get("label")
            ]
            disc_txt = ", ".join(discs) if discs else "—"
            pat = f" · Pattern `{svc.get('pattern')}`" if svc.get("pattern") else ""
            st.markdown(
                f"- **{svc.get('name')}** ({svc.get('service_type')}) · "
                f"{svc.get('num_apps')} apps @ ${float(svc.get('price') or 0):.2f} · "
                f"Disc: {disc_txt} · "
                f"Base ${float(svc.get('line_base') or 0):.2f} · "
                f"Tax ${float(svc.get('line_tax') or 0):.2f} · "
                f"**Line ${float(svc.get('line_total') or 0):.2f}**{pat}"
            )
    else:
        st.caption("No service lines stored.")

    if show_pdf_button:
        pdf = build_submission_snapshot_pdf(sub)
        st.download_button(
            "📄 Download read-only full submission (PDF)",
            data=pdf,
            file_name=f"submission_{sub.get('id')}_snapshot.pdf",
            mime="application/pdf",
            key=f"snap_pdf_{sub.get('id')}",
        )
