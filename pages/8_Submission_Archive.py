"""
Full chronological archive of all sale submissions over time.
"""
import streamlit as st
import json
import pandas as pd
from utils.theme import apply_theme
from utils.db import init_db, get_submissions_filtered, get_config

st.set_page_config(page_title="Submission Archive", page_icon="📚", layout="wide")
apply_theme()
init_db()

st.title("📚 Submission Archive")
st.caption("Complete history of exception sales over time — all statuses.")

# Slicers
c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.5, 2])
with c1:
    period = st.selectbox("Time period", ["all", "week", "month", "year"],
                          format_func=lambda x: {"all": "All time", "week": "Last 7 days",
                                                  "month": "Last 30 days", "year": "Last 12 months"}[x])
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
    ]

st.markdown(f"**{len(subs)}** submission(s)")

if not subs:
    st.info("No submissions match these filters.")
    st.stop()

# Summary metrics for filtered set
completed = sum(1 for s in subs if s["status"] == "completed")
kicked = sum(1 for s in subs if s["status"] == "kicked")
revenue = sum(float(s.get("grand_total") or 0) for s in subs if s["status"] == "completed")
m1, m2, m3, m4 = st.columns(4)
m1.metric("In view", len(subs))
m2.metric("Completed", completed)
m3.metric("Kicked", kicked)
m4.metric("Completed $", f"${revenue:,.0f}")

# Table
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
        "Kick reason": s.get("kick_reason") or "",
        "Processor": s.get("admin_user") or "",
    })

df = pd.DataFrame(rows)
st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    height=420,
    column_config={
        "Total $": st.column_config.NumberColumn(format="$%.2f"),
        "Status": st.column_config.TextColumn(width="small"),
        "ID": st.column_config.NumberColumn(width="small"),
    },
)

# Detail expander for selected
st.markdown("---")
st.subheader("Submission detail")
ids = [s["id"] for s in subs]
pick = st.selectbox("Open submission #", ids)
chosen = next((s for s in subs if s["id"] == pick), None)
if chosen:
    badge = f'<span class="badge-{chosen["status"]}">{chosen["status"].upper()}</span>'
    st.markdown(badge, unsafe_allow_html=True)
    d1, d2 = st.columns(2)
    with d1:
        st.write(f"**Customer:** {chosen.get('cust_first')} {chosen.get('cust_last')}")
        st.write(f"**Phone:** {chosen.get('cust_phone')} · **Email:** {chosen.get('cust_email') or '—'}")
        st.write(f"**Address:** {chosen.get('cust_street')}, {chosen.get('cust_city')}, "
                 f"{chosen.get('cust_state')} {chosen.get('cust_zip')}")
        st.write(f"**Rep:** {chosen.get('rep_first')} {chosen.get('rep_last')} ({chosen.get('emp_id')})")
        st.write(f"**Region / BU:** {chosen.get('region')} / {chosen.get('business_unit')}")
        st.write(f"**Channel:** {chosen.get('sales_channel') or '—'}")
        st.write(f"**Payment:** {chosen.get('payment_type')} · Prepay {chosen.get('prepay_pct') or 0}%")
    with d2:
        st.write(f"**Exception:** {chosen.get('exception_reason')}")
        st.write(f"**Sales notes:** {chosen.get('sales_notes') or '—'}")
        st.write(f"**Processor:** {chosen.get('admin_user') or '—'}")
        st.write(f"**Admin notes:** {chosen.get('admin_notes') or '—'}")
        if chosen.get("kick_reason"):
            st.error(f"Kick: {chosen['kick_reason']}")
        st.metric("Grand total", f"${float(chosen.get('grand_total') or 0):.2f}")
        services = json.loads(chosen.get("services_json") or "[]")
        for svc in services:
            pat = f" `{svc.get('pattern')}`" if svc.get("pattern") else ""
            st.write(f"• {svc.get('name')} ×{svc.get('num_apps')} @${float(svc.get('price') or 0):.2f}{pat}")

# CSV export
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Export filtered archive (CSV)", data=csv,
                   file_name="submission_archive.csv", mime="text/csv")
