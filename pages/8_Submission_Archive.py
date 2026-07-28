"""
Full chronological archive — view, edit, delete submissions.
"""
import json
import streamlit as st
import pandas as pd
from utils.theme import apply_theme
from utils.db import (
    init_db, get_submissions_filtered, get_config, get_submission,
    update_full_submission, delete_submission, list_processors,
    normalize_processor_name,
)
from utils.submission_view import render_submission_detail, build_submission_snapshot_pdf
from utils.validation import validate_submission, validate_processor_name

st.set_page_config(page_title="Submission Archive", page_icon="📚", layout="wide")
apply_theme()
init_db()

st.title("📚 Submission Archive")
st.caption("Complete history — view full sale details, download PDF snapshot, edit or delete to correct errors.")

# Slicers
c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.5, 2])
with c1:
    period = st.selectbox(
        "Time period",
        ["all", "week", "month", "year"],
        format_func=lambda x: {
            "all": "All time", "week": "Last 7 days",
            "month": "Last 30 days", "year": "Last 12 months",
        }[x],
    )
with c2:
    status = st.selectbox("Status", ["all", "pending", "processing", "audit", "completed", "kicked"])
with c3:
    regions = ["All"] + get_config("regions")
    region = st.selectbox("Region", regions)
with c4:
    search = st.text_input("Search (customer, emp ID, #, reason)", placeholder="Type to filter…")

subs = get_submissions_filtered(
    status=None if status == "all" else status,
    period=period,
    region=None if region == "All" else region,
    limit=2000,
)
if search and search.strip():
    q = search.strip().lower()
    subs = [
        s for s in subs
        if q in str(s.get("id", "")).lower()
        or q in (s.get("cust_last") or "").lower()
        or q in (s.get("cust_first") or "").lower()
        or q in (s.get("emp_id") or "").lower()
        or q in (s.get("exception_reason") or "").lower()
        or q in (s.get("kick_reason") or "").lower()
        or q in (s.get("region") or "").lower()
        or q in (s.get("admin_user") or "").lower()
    ]

st.markdown(f"**{len(subs)}** submission(s)")
if not subs:
    st.info("No submissions match these filters.")
    st.stop()

completed = sum(1 for s in subs if s["status"] == "completed")
kicked = sum(1 for s in subs if s["status"] == "kicked")
revenue = sum(float(s.get("grand_total") or 0) for s in subs if s["status"] == "completed")
m1, m2, m3, m4 = st.columns(4)
m1.metric("In view", len(subs))
m2.metric("Completed", completed)
m3.metric("Kicked", kicked)
m4.metric("Completed $", f"${revenue:,.0f}")

rows = []
for s in subs:
    rows.append({
        "ID": s["id"],
        "Submitted": (s.get("created_at") or "")[:19].replace("T", " "),
        "Status": s.get("status"),
        "Customer": f"{s.get('cust_last', '')}, {s.get('cust_first', '')}",
        "Region": s.get("region"),
        "Emp ID": s.get("emp_id"),
        "Rep": f"{s.get('rep_first', '')} {s.get('rep_last', '')}".strip(),
        "Total $": round(float(s.get("grand_total") or 0), 2),
        "Exception reason": s.get("exception_reason"),
        "Processor": s.get("admin_user") or "",
        "Kick reason": s.get("kick_reason") or "",
    })
df = pd.DataFrame(rows)
st.dataframe(
    df, use_container_width=True, hide_index=True, height=320,
    column_config={
        "Total $": st.column_config.NumberColumn(format="$%.2f"),
        "ID": st.column_config.NumberColumn(width="small"),
        "Status": st.column_config.TextColumn(width="small"),
    },
)

st.markdown("---")
st.subheader("Record detail · edit · delete")

ids = [s["id"] for s in subs]
pick = st.selectbox("Select submission #", ids)
chosen = get_submission(pick) or next((s for s in subs if s["id"] == pick), None)
if not chosen:
    st.stop()

# Full detail + PDF snapshot
render_submission_detail(chosen, show_pdf_button=True)

st.markdown("---")
# Actor required for mutations
procs = list_processors()
actor_choice = st.selectbox(
    "Your name (required to edit or delete)",
    options=[""] + procs + ["— type new —"],
    key="arch_actor_sel",
)
if actor_choice == "— type new —":
    actor_raw = st.text_input("Type processor name", key="arch_actor_new")
else:
    actor_raw = actor_choice
actor_ok = validate_processor_name(actor_raw)
can_mutate = actor_ok.ok

mode = st.radio("Action", ["View only", "Edit record", "Delete record"], horizontal=True)

if mode == "Edit record":
    if not can_mutate:
        st.warning("Enter a valid processor name before saving edits.")
    st.markdown("#### Edit fields")
    e1, e2, e3 = st.columns(3)
    with e1:
        cust_first = st.text_input("First name", value=chosen.get("cust_first") or "")
        cust_phone = st.text_input("Phone", value=chosen.get("cust_phone") or "")
        cust_street = st.text_input("Street", value=chosen.get("cust_street") or "")
        cust_state = st.text_input("State", value=chosen.get("cust_state") or "", max_chars=2)
        emp_id = st.text_input("Emp ID", value=chosen.get("emp_id") or "")
        business_unit = st.text_input("Business unit", value=chosen.get("business_unit") or "")
    with e2:
        cust_last = st.text_input("Last name", value=chosen.get("cust_last") or "")
        cust_mobile = st.text_input("Mobile", value=chosen.get("cust_mobile") or "")
        cust_city = st.text_input("City", value=chosen.get("cust_city") or "")
        cust_zip = st.text_input("ZIP", value=chosen.get("cust_zip") or "")
        rep_first = st.text_input("Rep first", value=chosen.get("rep_first") or "")
        region = st.text_input("Region", value=chosen.get("region") or "")
    with e3:
        cust_email = st.text_input("Email", value=chosen.get("cust_email") or "")
        grass_type = st.text_input("Grass", value=chosen.get("grass_type") or "")
        property_sqft = st.number_input("Sq ft", value=float(chosen.get("property_sqft") or 0))
        rep_last = st.text_input("Rep last", value=chosen.get("rep_last") or "")
        rep_email = st.text_input("Rep email", value=chosen.get("rep_email") or "")
        sales_channel = st.text_input("Channel", value=chosen.get("sales_channel") or "")

    payment_type = st.selectbox(
        "Payment type",
        ["prepay", "easpay", "invoice"],
        index=["prepay", "easpay", "invoice"].index(chosen.get("payment_type") or "invoice")
        if (chosen.get("payment_type") in ("prepay", "easpay", "invoice")) else 2,
    )
    prepay_pct = st.selectbox("Prepay %", [0, 5, 7, 10],
                              index=[0, 5, 7, 10].index(int(chosen.get("prepay_pct") or 0))
                              if int(chosen.get("prepay_pct") or 0) in (0, 5, 7, 10) else 0)
    exception_reason = st.text_input("Exception reason", value=chosen.get("exception_reason") or "")
    sales_notes = st.text_area("Sales notes", value=chosen.get("sales_notes") or "", height=80)
    new_status = st.selectbox(
        "Status",
        ["pending", "processing", "audit", "completed", "kicked"],
        index=["pending", "processing", "audit", "completed", "kicked"].index(chosen.get("status") or "pending")
        if chosen.get("status") in ("pending", "processing", "audit", "completed", "kicked") else 0,
    )
    subtotal = st.number_input("Subtotal", value=float(chosen.get("subtotal") or 0), format="%.2f")
    total_discount = st.number_input("Total discount", value=float(chosen.get("total_discount") or 0), format="%.2f")
    total_tax = st.number_input("Total tax", value=float(chosen.get("total_tax") or 0), format="%.2f")
    grand_total = st.number_input("Grand total", value=float(chosen.get("grand_total") or 0), format="%.2f")

    # Keep existing services JSON unless user pastes replacement
    st.caption("Services JSON (advanced — leave unchanged unless correcting program lines)")
    services_raw = st.text_area(
        "services_json",
        value=chosen.get("services_json") or "[]",
        height=120,
    )

    if st.button("💾 Save corrections", type="primary", disabled=not can_mutate):
        try:
            services = json.loads(services_raw)
        except Exception:
            st.error("services_json is not valid JSON")
            st.stop()
        payload = {
            "cust_first": cust_first, "cust_last": cust_last,
            "cust_phone": cust_phone, "cust_mobile": cust_mobile, "cust_email": cust_email,
            "cust_street": cust_street, "cust_city": cust_city,
            "cust_state": cust_state.upper(), "cust_zip": cust_zip,
            "property_sqft": property_sqft, "grass_type": grass_type,
            "areas_serviced": json.loads(chosen.get("areas_serviced") or "[]"),
            "special_params": json.loads(chosen.get("special_params") or "[]"),
            "services": services,
            "emp_id": emp_id, "rep_first": rep_first, "rep_last": rep_last, "rep_email": rep_email,
            "business_unit": business_unit, "region": region, "sales_channel": sales_channel,
            "payment_type": payment_type, "prepay_pct": prepay_pct,
            "subtotal": subtotal, "total_discount": total_discount,
            "total_tax": total_tax, "grand_total": grand_total,
            "exception_reason": exception_reason, "sales_notes": sales_notes,
            "status": new_status,
        }
        result = validate_submission(payload)
        for w in result.warnings:
            st.warning(w)
        if not result.ok:
            for e in result.errors:
                st.error(e)
        else:
            actor = normalize_processor_name(actor_raw)
            if update_full_submission(pick, payload, actor):
                st.success(f"Submission #{pick} updated by {actor}.")
                st.rerun()
            else:
                st.error("Update failed.")

elif mode == "Delete record":
    st.error(
        f"Permanently delete submission **#{pick}** "
        f"({chosen.get('cust_last')}, {chosen.get('cust_first')} · "
        f"${float(chosen.get('grand_total') or 0):.2f})? This cannot be undone."
    )
    confirm = st.text_input("Type DELETE to confirm")
    if st.button("🗑 Permanently delete", type="primary", disabled=not can_mutate):
        if not can_mutate:
            st.error("Processor name required.")
        elif confirm.strip().upper() != "DELETE":
            st.error("Type DELETE to confirm.")
        else:
            actor = normalize_processor_name(actor_raw)
            if delete_submission(pick, actor):
                st.success(f"Submission #{pick} deleted by {actor}.")
                st.rerun()
            else:
                st.error("Delete failed.")

csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export filtered archive (CSV)", data=csv,
                   file_name="submission_archive.csv", mime="text/csv")
