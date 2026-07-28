"""
Admin Queue – process pending / processing submissions.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import (
    init_db, verify_admin, get_admin_display, get_submissions,
    get_submission, update_submission_status, get_config, log_audit
)

st.set_page_config(page_title="Admin Queue", page_icon="🛠️", layout="wide")
apply_theme()
init_db()

st.title("🛠️ Admin Processing Queue")

# Auth
if "admin_user" not in st.session_state:
    st.session_state.admin_user = None

if not st.session_state.admin_user:
    st.subheader("Admin Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        if verify_admin(u, p):
            st.session_state.admin_user = u
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

actor = st.session_state.admin_user
st.sidebar.success(f"Logged in as {get_admin_display(actor)}")
if st.sidebar.button("Logout"):
    st.session_state.admin_user = None
    st.rerun()

# Filters
status_filter = st.selectbox("Filter by status", ["pending", "processing", "all active"], index=0)
if status_filter == "all active":
    subs = [s for s in get_submissions(limit=300) if s["status"] in ("pending", "processing")]
else:
    subs = get_submissions(status=status_filter, limit=300)

st.caption(f"{len(subs)} submission(s)")

if not subs:
    st.info("No submissions in this queue.")
    st.stop()

# List + detail
for s in subs:
    badge = f'<span class="badge-{s["status"]}">{s["status"].upper()}</span>'
    with st.expander(
        f"#{s['id']} | {s['cust_last']}, {s['cust_first']} | {s['region']} | ${s['grand_total']:.2f} | {s['emp_id']}  {badge}",
        expanded=False
    ):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"**Created:** {s['created_at']}")
            st.markdown(f"**Customer:** {s['cust_first']} {s['cust_last']}")
            st.markdown(f"**Phone:** {s['cust_phone']} / {s['cust_mobile']}")
            st.markdown(f"**Email:** {s['cust_email']}")
            st.markdown(f"**Address:** {s['cust_street']}, {s['cust_city']}, {s['cust_state']} {s['cust_zip']}")
            st.markdown(f"**Sq Ft:** {s['property_sqft']} | Grass: {s['grass_type']}")
            areas = json.loads(s.get("areas_serviced") or "[]")
            special = json.loads(s.get("special_params") or "[]")
            st.markdown(f"**Areas:** {', '.join(areas) or '—'} | **Special:** {', '.join(special) or '—'}")
        with c2:
            st.markdown(f"**Rep:** {s['rep_first']} {s['rep_last']} ({s['emp_id']})")
            st.markdown(f"**BU / Region:** {s['business_unit']} / {s['region']}")
            st.markdown(f"**Channel:** {s['sales_channel']}")
            st.markdown(f"**Payment:** {s['payment_type']} | Prepay {s['prepay_pct']}%")
            st.markdown(f"**Reason:** {s['exception_reason']}")
            st.markdown(f"**Sales notes:** {s['sales_notes'] or '—'}")
        with c3:
            st.metric("Grand Total", f"${s['grand_total']:.2f}")
            st.markdown(f"Sub ${s['subtotal']:.2f} · Disc ${s['total_discount']:.2f} · Tax ${s['total_tax']:.2f}")
            services = json.loads(s.get("services_json") or "[]")
            st.markdown("**Services:**")
            for svc in services:
                pat = f" `{svc.get('pattern')}`" if svc.get("pattern") else ""
                st.write(f"• {svc.get('name')} ×{svc.get('num_apps')} @${svc.get('price',0):.2f} = ${svc.get('line_total',0):.2f}{pat}")

        st.markdown("---")
        admin_notes = st.text_area("Admin notes", key=f"an_{s['id']}", value=s.get("admin_notes") or "")
        kick_reasons = get_config("kick_reasons")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            if st.button("✅ Mark Completed", key=f"comp_{s['id']}", type="primary"):
                update_submission_status(s["id"], "completed", actor, admin_notes)
                st.success("Marked completed – sales rep notified.")
                st.rerun()
        with k2:
            if st.button("🔄 Set Processing", key=f"proc_{s['id']}"):
                update_submission_status(s["id"], "processing", actor, admin_notes)
                st.rerun()
        with k3:
            if st.button("🔍 Move to Audit", key=f"aud_{s['id']}"):
                update_submission_status(s["id"], "audit", actor, admin_notes)
                st.rerun()
        with k4:
            kick_r = st.selectbox("Kick reason", [""] + kick_reasons, key=f"kr_{s['id']}")
            if st.button("❌ Kick / Reject", key=f"kick_{s['id']}"):
                if not kick_r:
                    st.error("Select a kick reason")
                else:
                    update_submission_status(s["id"], "kicked", actor, admin_notes, kick_r)
                    st.warning("Kicked – moved to archive, sales rep notified.")
                    st.rerun()
