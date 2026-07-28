"""
Kick Archive – read-only history of rejected sales. Open access.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import init_db, get_submissions

st.set_page_config(page_title="Kick Archive", page_icon="📦", layout="wide")
apply_theme()
init_db()

st.title("📦 Kick Archive")
st.caption("Rejected / kicked submissions for later review. Read-only.")

subs = get_submissions(status="kicked", limit=500)
st.metric("Kicked submissions", len(subs))

if not subs:
    st.info("Archive is empty.")
    st.stop()

search = st.text_input("Filter by customer, emp ID, or kick reason")
if search and search.strip():
    q = search.strip().lower()
    subs = [
        s for s in subs
        if q in (s.get("cust_last") or "").lower()
        or q in (s.get("emp_id") or "").lower()
        or q in (s.get("kick_reason") or "").lower()
        or q in str(s.get("id", ""))
    ]

for s in subs:
    with st.expander(
        f"#{s['id']} · {s.get('cust_last')}, {s.get('cust_first')} · "
        f"${float(s.get('grand_total') or 0):.2f} · Kick: {s.get('kick_reason') or '—'}"
    ):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Kicked at:** {s.get('processed_at') or s.get('updated_at')}")
            st.write(f"**By:** {s.get('admin_user') or '—'}")
            st.write(f"**Kick reason:** {s.get('kick_reason')}")
            st.write(f"**Admin notes:** {s.get('admin_notes') or '—'}")
            st.write(f"**Original exception reason:** {s.get('exception_reason')}")
            st.write(f"**Sales notes:** {s.get('sales_notes') or '—'}")
        with c2:
            st.write(f"**Customer:** {s.get('cust_first')} {s.get('cust_last')} — {s.get('cust_phone')}")
            st.write(f"**Rep:** {s.get('rep_first')} {s.get('rep_last')} ({s.get('emp_id')})")
            services = json.loads(s.get("services_json") or "[]")
            for svc in services:
                st.write(f"• {svc.get('name')} ×{svc.get('num_apps')}")
            st.metric("Would-have-been total", f"${float(s.get('grand_total') or 0):.2f}")
