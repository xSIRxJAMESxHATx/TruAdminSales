"""
Admin Queue – process pending / processing submissions.
Open access (no password). Actor name optional for audit trail.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import init_db, get_submissions, update_submission_status, get_config, get_analytics_data

st.set_page_config(page_title="Admin Queue", page_icon="🛠️", layout="wide")
apply_theme()
init_db()

st.title("🛠️ Admin Processing Queue")
st.caption("Review exception sales, enter into system, move to audit, or kick with reason. Open to sales & admin teams.")

# Actor for audit trail (optional)
actor = st.sidebar.text_input("Your name / ID (for audit log)", value="processor", key="admin_actor")
st.sidebar.markdown("---")
st.sidebar.markdown("**Quick tips**")
st.sidebar.markdown(
    "- Set **Processing** while you work a sale\n"
    "- **Completed** after system entry\n"
    "- **Audit** when customer contact is needed\n"
    "- **Kick** requires a reason"
)

# KPI strip
try:
    totals = get_analytics_data().get("totals") or {}
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Pending", int(totals.get("pending") or 0))
    k2.metric("Processing", int(totals.get("processing") or 0) if "processing" in (totals or {}) else
              len(get_submissions(status="processing", limit=500)))
    k3.metric("In audit", int(totals.get("audit") or 0))
    k4.metric("Completed (all time)", int(totals.get("completed") or 0))
except Exception:
    pass

st.markdown("---")

# Filters
f1, f2 = st.columns([2, 1])
with f1:
    status_filter = st.radio(
        "Queue filter",
        ["pending", "processing", "all active"],
        horizontal=True,
        index=0,
    )
with f2:
    search = st.text_input("Search customer / emp ID / #", placeholder="optional filter")

if status_filter == "all active":
    subs = [s for s in get_submissions(limit=400) if s["status"] in ("pending", "processing")]
else:
    subs = get_submissions(status=status_filter, limit=400)

if search and search.strip():
    q = search.strip().lower()
    subs = [
        s for s in subs
        if q in str(s.get("id", "")).lower()
        or q in (s.get("cust_last") or "").lower()
        or q in (s.get("cust_first") or "").lower()
        or q in (s.get("emp_id") or "").lower()
    ]

st.caption(f"**{len(subs)}** submission(s) in view")

if not subs:
    st.info("No submissions in this queue. New sales appear here after a rep submits.")
    st.stop()

kick_reasons = get_config("kick_reasons")

for s in subs:
    status = s["status"]
    badge = f'<span class="badge-{status}">{status.upper()}</span>'
    header = (
        f"**#{s['id']}** · {s.get('cust_last','')}, {s.get('cust_first','')} · "
        f"{s.get('region','')} · **${float(s.get('grand_total') or 0):.2f}** · "
        f"Rep {s.get('emp_id','')}  "
    )
    with st.expander(header, expanded=(status == "pending")):
        st.markdown(badge, unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.2, 1.2, 1])
        with c1:
            st.markdown("**Customer**")
            st.write(f"{s.get('cust_first')} {s.get('cust_last')}")
            st.write(f"📞 {s.get('cust_phone')}  ·  {s.get('cust_mobile') or '—'}")
            st.write(f"✉️ {s.get('cust_email') or '—'}")
            st.write(f"📍 {s.get('cust_street')}, {s.get('cust_city')}, {s.get('cust_state')} {s.get('cust_zip')}")
            areas = json.loads(s.get("areas_serviced") or "[]")
            special = json.loads(s.get("special_params") or "[]")
            st.caption(f"Sq ft: {s.get('property_sqft') or '—'} · Grass: {s.get('grass_type') or '—'}")
            st.caption(f"Areas: {', '.join(areas) or '—'} · Special: {', '.join(special) or '—'}")
        with c2:
            st.markdown("**Rep & sale**")
            st.write(f"{s.get('rep_first')} {s.get('rep_last')} ({s.get('emp_id')})")
            st.write(f"Email: {s.get('rep_email') or '—'}")
            st.write(f"{s.get('business_unit')} / {s.get('region')}")
            st.write(f"Channel: {s.get('sales_channel') or '—'}")
            st.write(f"Payment: **{s.get('payment_type')}** · Prepay {s.get('prepay_pct') or 0}%")
            st.write(f"Reason: *{s.get('exception_reason') or '—'}*")
            if s.get("sales_notes"):
                st.info(s["sales_notes"])
        with c3:
            st.metric("Grand total", f"${float(s.get('grand_total') or 0):.2f}")
            st.caption(
                f"Sub ${float(s.get('subtotal') or 0):.2f} · "
                f"Disc ${float(s.get('total_discount') or 0):.2f} · "
                f"Tax ${float(s.get('total_tax') or 0):.2f}"
            )
            services = json.loads(s.get("services_json") or "[]")
            st.markdown("**Services**")
            for svc in services:
                pat = f" `{svc.get('pattern')}`" if svc.get("pattern") else ""
                st.write(
                    f"• {svc.get('name')} ×{svc.get('num_apps')} "
                    f"@${float(svc.get('price') or 0):.2f} → "
                    f"${float(svc.get('line_total') or 0):.2f}{pat}"
                )

        st.markdown("---")
        admin_notes = st.text_area(
            "Processor notes",
            key=f"an_{s['id']}",
            value=s.get("admin_notes") or "",
            height=70,
            placeholder="Optional notes for the rep / audit trail",
        )
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            if st.button("✅ Complete", key=f"comp_{s['id']}", type="primary", use_container_width=True):
                update_submission_status(s["id"], "completed", actor, admin_notes)
                st.success("Completed — rep notified (in-app + email if configured).")
                st.rerun()
        with b2:
            if st.button("🔄 Processing", key=f"proc_{s['id']}", use_container_width=True):
                update_submission_status(s["id"], "processing", actor, admin_notes)
                st.rerun()
        with b3:
            if st.button("🔍 To Audit", key=f"aud_{s['id']}", use_container_width=True):
                update_submission_status(s["id"], "audit", actor, admin_notes)
                st.rerun()
        with b4:
            kick_r = st.selectbox("Kick reason", [""] + kick_reasons, key=f"kr_{s['id']}")
            if st.button("❌ Kick", key=f"kick_{s['id']}", use_container_width=True):
                if not kick_r:
                    st.error("Select a kick reason")
                else:
                    update_submission_status(s["id"], "kicked", actor, admin_notes, kick_r)
                    st.warning("Kicked — rep notified.")
                    st.rerun()
