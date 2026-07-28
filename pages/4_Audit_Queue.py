"""
Audit Queue – sales moved here for customer contact / verification.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import (
    init_db, verify_admin, get_admin_display, get_submissions,
    update_submission_status, get_config
)

st.set_page_config(page_title="Audit Queue", page_icon="🔍", layout="wide")
apply_theme()
init_db()

st.title("🔍 Audit Queue")
st.caption("Submissions requiring customer contact or additional verification before final status.")

if "admin_user" not in st.session_state:
    st.session_state.admin_user = None

if not st.session_state.admin_user:
    st.subheader("Admin Login")
    u = st.text_input("Username", key="aud_u")
    p = st.text_input("Password", type="password", key="aud_p")
    if st.button("Login", key="aud_login"):
        if verify_admin(u, p):
            st.session_state.admin_user = u
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

actor = st.session_state.admin_user
st.sidebar.success(f"Logged in as {get_admin_display(actor)}")
if st.sidebar.button("Logout", key="aud_logout"):
    st.session_state.admin_user = None
    st.rerun()

subs = get_submissions(status="audit", limit=200)
st.caption(f"{len(subs)} item(s) in audit")

if not subs:
    st.info("Audit queue is empty.")
    st.stop()

kick_reasons = get_config("kick_reasons")

for s in subs:
    with st.expander(f"#{s['id']} | {s['cust_last']}, {s['cust_first']} | ${s['grand_total']:.2f} | {s['emp_id']}", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Customer:** {s['cust_first']} {s['cust_last']}")
            st.markdown(f"**Phone:** {s['cust_phone']} / Mobile: {s['cust_mobile']}")
            st.markdown(f"**Email:** {s['cust_email']}")
            st.markdown(f"**Address:** {s['cust_street']}, {s['cust_city']}, {s['cust_state']} {s['cust_zip']}")
            st.markdown(f"**Rep:** {s['rep_first']} {s['rep_last']} ({s['emp_id']}) – {s['region']}")
            st.markdown(f"**Exception reason:** {s['exception_reason']}")
            st.markdown(f"**Sales notes:** {s['sales_notes'] or '—'}")
        with c2:
            services = json.loads(s.get("services_json") or "[]")
            st.markdown("**Services:**")
            for svc in services:
                st.write(f"• {svc.get('name')} ×{svc.get('num_apps')} @${svc.get('price',0):.2f}")
            st.metric("Customer Total", f"${s['grand_total']:.2f}")
            if s.get("admin_notes"):
                st.info(f"Prior admin notes: {s['admin_notes']}")

        notes = st.text_area("Audit notes / contact outcome", key=f"aud_n_{s['id']}")
        b1, b2 = st.columns(2)
        with b1:
            if st.button("✅ Complete after Audit", key=f"aud_ok_{s['id']}", type="primary"):
                update_submission_status(s["id"], "completed", actor, notes)
                st.success("Completed – rep notified.")
                st.rerun()
        with b2:
            kr = st.selectbox("Kick reason", [""] + kick_reasons, key=f"aud_kr_{s['id']}")
            if st.button("❌ Kick after Audit", key=f"aud_kick_{s['id']}"):
                if not kr:
                    st.error("Select kick reason")
                else:
                    update_submission_status(s["id"], "kicked", actor, notes, kr)
                    st.warning("Kicked – rep notified.")
                    st.rerun()
