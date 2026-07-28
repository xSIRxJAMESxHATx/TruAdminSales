"""
Audit Queue – customer-contact verification. Open access.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import init_db, get_submissions, update_submission_status, get_config, list_processors, normalize_processor_name
from utils.validation import validate_processor_name

st.set_page_config(page_title="Audit Queue", page_icon="🔍", layout="wide")
apply_theme()
init_db()

st.title("🔍 Audit Queue")
st.caption("Sales requiring customer contact or extra verification before final status.")

_procs = list_processors()
_sel = st.sidebar.selectbox("Your name (required)", options=[""] + _procs + ["— type new —"], key="aud_actor_sel")
if _sel == "— type new —":
    actor = st.sidebar.text_input("Type your full name", key="aud_actor", placeholder="e.g. Jane Smith")
else:
    actor = _sel
can_process = validate_processor_name(actor).ok
if not can_process:
    st.sidebar.warning("Enter your name before completing audit actions.")
    st.warning("Enter your name in the sidebar to enable audit actions.")

subs = get_submissions(status="audit", limit=200)
st.metric("Items in audit", len(subs))

if not subs:
    st.info("Audit queue is empty.")
    st.stop()

kick_reasons = get_config("kick_reasons")

for s in subs:
    with st.expander(
        f"#{s['id']} · {s.get('cust_last')}, {s.get('cust_first')} · ${float(s.get('grand_total') or 0):.2f} · {s.get('emp_id')}",
        expanded=True,
    ):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Customer**")
            st.write(f"{s.get('cust_first')} {s.get('cust_last')}")
            st.write(f"📞 {s.get('cust_phone')} / {s.get('cust_mobile') or '—'}")
            st.write(f"✉️ {s.get('cust_email') or '—'}")
            st.write(f"📍 {s.get('cust_street')}, {s.get('cust_city')}, {s.get('cust_state')} {s.get('cust_zip')}")
            st.write(f"**Rep:** {s.get('rep_first')} {s.get('rep_last')} ({s.get('emp_id')}) — {s.get('region')}")
            st.write(f"**Exception:** {s.get('exception_reason')}")
            if s.get("sales_notes"):
                st.info(s["sales_notes"])
            if s.get("admin_notes"):
                st.warning(f"Prior processor notes: {s['admin_notes']}")
        with c2:
            services = json.loads(s.get("services_json") or "[]")
            st.markdown("**Services**")
            for svc in services:
                st.write(f"• {svc.get('name')} ×{svc.get('num_apps')} @${float(svc.get('price') or 0):.2f}")
            st.metric("Customer total", f"${float(s.get('grand_total') or 0):.2f}")

        notes = st.text_area("Audit notes / contact outcome", key=f"aud_n_{s['id']}", height=80)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("✅ Complete after audit", key=f"aud_ok_{s['id']}", type="primary", use_container_width=True):
                if not can_process:
                    st.error("Enter your name in the sidebar first.")
                else:
                    update_submission_status(s["id"], "completed", actor.strip(), notes)
                    st.success("Completed — rep notified.")
                    st.rerun()
        with b2:
            kr = st.selectbox("Kick reason", [""] + kick_reasons, key=f"aud_kr_{s['id']}")
            if st.button("❌ Kick after audit", key=f"aud_kick_{s['id']}", use_container_width=True):
                if not can_process:
                    st.error("Enter your name in the sidebar first.")
                elif not kr:
                    st.error("Select kick reason")
                else:
                    update_submission_status(s["id"], "kicked", actor.strip(), notes, kr)
                    st.warning("Kicked — rep notified.")
                    st.rerun()
