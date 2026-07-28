"""
Sales rep view of their own submissions + notifications.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import init_db, get_submissions, get_notifications, mark_notifications_read, get_submission

st.set_page_config(page_title="My Submissions", page_icon="📬", layout="wide")
apply_theme()
init_db()

st.title("📬 My Submissions & Notifications")

emp_id = st.text_input("Enter your Employee ID to view your submissions", key="my_emp")
if not emp_id:
    st.info("Enter your Employee ID above.")
    st.stop()

# Notifications
notifs = get_notifications(emp_id)
unread = [n for n in notifs if not n["read_flag"]]
if unread:
    st.warning(f"You have **{len(unread)}** unread notification(s).")
    for n in unread:
        st.info(f"**#{n['submission_id']}** – {n['message']}  \n_{n['created_at']}_")
    if st.button("Mark all as read"):
        mark_notifications_read(emp_id)
        st.rerun()
else:
    st.success("No unread notifications.")

st.markdown("---")
subs = get_submissions(emp_id=emp_id)
st.subheader(f"Your Submissions ({len(subs)})")

if not subs:
    st.info("No submissions found for this Employee ID.")
else:
    for s in subs:
        status = s["status"]
        badge = f'<span class="badge-{status}">{status.upper()}</span>'
        with st.expander(f"#{s['id']} – {s['cust_first']} {s['cust_last']} – ${s['grand_total']:.2f}  {badge}", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Created:** {s['created_at']}")
                st.markdown(f"**Customer:** {s['cust_first']} {s['cust_last']}")
                st.markdown(f"**Phone:** {s['cust_phone']}")
                st.markdown(f"**Address:** {s['cust_street']}, {s['cust_city']}, {s['cust_state']} {s['cust_zip']}")
                st.markdown(f"**Exception Reason:** {s['exception_reason']}")
            with c2:
                st.markdown(f"**Status:** {status}")
                st.markdown(f"**Payment:** {s['payment_type']} (prepay {s['prepay_pct']}%)")
                st.markdown(f"**Totals:** Sub ${s['subtotal']:.2f} | Disc ${s['total_discount']:.2f} | Tax ${s['total_tax']:.2f} | **Grand ${s['grand_total']:.2f}**")
                if s.get("admin_notes"):
                    st.markdown(f"**Admin notes:** {s['admin_notes']}")
                if s.get("kick_reason"):
                    st.error(f"**Kick reason:** {s['kick_reason']}")
            services = json.loads(s.get("services_json") or "[]")
            if services:
                st.markdown("**Services:**")
                for svc in services:
                    pat = f" | Pattern: `{svc.get('pattern')}`" if svc.get("pattern") else ""
                    st.write(f"- {svc.get('name')} × {svc.get('num_apps')} @ ${svc.get('price', 0):.2f} → ${svc.get('line_total', 0):.2f}{pat}")
            if s.get("sales_notes"):
                st.markdown(f"**Your notes:** {s['sales_notes']}")
