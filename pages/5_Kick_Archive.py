"""
Kick Archive – read-only review of rejected sales.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import init_db, verify_admin, get_admin_display, get_submissions

st.set_page_config(page_title="Kick Archive", page_icon="📦", layout="wide")
apply_theme()
init_db()

st.title("📦 Kick Archive")
st.caption("Rejected / kicked submissions for later review. Read-only.")

if "admin_user" not in st.session_state:
    st.session_state.admin_user = None

if not st.session_state.admin_user:
    st.subheader("Admin Login")
    u = st.text_input("Username", key="ka_u")
    p = st.text_input("Password", type="password", key="ka_p")
    if st.button("Login", key="ka_login"):
        if verify_admin(u, p):
            st.session_state.admin_user = u
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

st.sidebar.success(f"Logged in as {get_admin_display(st.session_state.admin_user)}")
if st.sidebar.button("Logout", key="ka_logout"):
    st.session_state.admin_user = None
    st.rerun()

subs = get_submissions(status="kicked", limit=500)
st.caption(f"{len(subs)} kicked submission(s)")

if not subs:
    st.info("Archive is empty.")
    st.stop()

for s in subs:
    with st.expander(f"#{s['id']} | {s['cust_last']}, {s['cust_first']} | ${s['grand_total']:.2f} | Kick: {s.get('kick_reason','—')}"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Kicked at:** {s.get('processed_at') or s['updated_at']}")
            st.markdown(f"**By:** {s.get('admin_user')}")
            st.markdown(f"**Kick reason:** {s.get('kick_reason')}")
            st.markdown(f"**Admin notes:** {s.get('admin_notes') or '—'}")
            st.markdown(f"**Original exception reason:** {s['exception_reason']}")
            st.markdown(f"**Sales notes:** {s['sales_notes'] or '—'}")
        with c2:
            st.markdown(f"**Customer:** {s['cust_first']} {s['cust_last']} – {s['cust_phone']}")
            st.markdown(f"**Rep:** {s['rep_first']} {s['rep_last']} ({s['emp_id']})")
            services = json.loads(s.get("services_json") or "[]")
            for svc in services:
                st.write(f"• {svc.get('name')} ×{svc.get('num_apps')}")
            st.metric("Would-have-been total", f"${s['grand_total']:.2f}")
