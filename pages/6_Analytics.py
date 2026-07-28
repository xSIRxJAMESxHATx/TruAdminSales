"""
Analytics – macro trends for sales & admin.
Sales team has read access; no write actions here.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.theme import apply_theme
from utils.db import init_db, get_analytics_data, get_submissions

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
apply_theme()
init_db()

st.title("📊 Sales Exception Analytics")
st.caption("Macro trends · submitters · processors · reasons · kicks. Read-only for all users.")

data = get_analytics_data()
totals = data.get("totals", {})

# KPI row
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Submissions", int(totals.get("total_subs") or 0))
k2.metric("Completed", int(totals.get("completed") or 0))
k3.metric("Kicked", int(totals.get("kicked") or 0))
k4.metric("Pending", int(totals.get("pending") or 0))
k5.metric("In Audit", int(totals.get("audit") or 0))
k6.metric("Total $ Volume", f"${totals.get('revenue', 0):,.2f}")

st.markdown("---")

# Charts
c1, c2 = st.columns(2)

with c1:
    st.subheader("Status Distribution")
    sc = data.get("status_counts") or {}
    if sc:
        df = pd.DataFrame({"status": list(sc.keys()), "count": list(sc.values())})
        fig = px.pie(df, names="status", values="count", color="status",
                     color_discrete_map={
                         "pending": "#ffb74d", "processing": "#64b5f6",
                         "audit": "#ba68c8", "completed": "#81c784", "kicked": "#e57373"
                     })
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet.")

with c2:
    st.subheader("Daily Volume (last 60 days)")
    daily = data.get("daily") or []
    if daily:
        df = pd.DataFrame(daily)
        fig = px.bar(df, x="day", y="cnt", labels={"cnt": "Submissions", "day": "Date"},
                     color_discrete_sequence=["#43a047"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No recent volume.")

c3, c4 = st.columns(2)
with c3:
    st.subheader("Top Submitters (Sales Reps)")
    reps = data.get("top_reps") or []
    if reps:
        st.dataframe(pd.DataFrame(reps), use_container_width=True, hide_index=True)
    else:
        st.info("No data.")

with c4:
    st.subheader("Top Processors (Admins)")
    admins = data.get("top_admins") or []
    if admins:
        st.dataframe(pd.DataFrame(admins), use_container_width=True, hide_index=True)
    else:
        st.info("No data.")

c5, c6 = st.columns(2)
with c5:
    st.subheader("Exception Reasons")
    reasons = data.get("reasons") or []
    if reasons:
        df = pd.DataFrame(reasons)
        fig = px.bar(df, x="cnt", y="reason", orientation="h", color_discrete_sequence=["#2e7d32"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data.")

with c6:
    st.subheader("Kick Reasons")
    kicks = data.get("kicks") or []
    if kicks:
        df = pd.DataFrame(kicks)
        fig = px.bar(df, x="cnt", y="reason", orientation="h", color_discrete_sequence=["#c62828"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No kicks recorded.")

st.markdown("---")
st.subheader("Recent Submissions Snapshot")
recent = get_submissions(limit=50)
if recent:
    df = pd.DataFrame(recent)[["id", "created_at", "status", "emp_id", "rep_first", "rep_last",
                                "cust_last", "region", "exception_reason", "grand_total", "kick_reason"]]
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No submissions yet.")
