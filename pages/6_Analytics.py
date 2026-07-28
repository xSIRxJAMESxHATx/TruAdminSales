"""
Analytics with time slicers, trend charts, and notes word-cloud analysis.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
from io import BytesIO

from utils.theme import apply_theme
from utils.db import (
    init_db, get_analytics_data, get_submissions_filtered,
    get_all_notes_text, get_config
)

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
apply_theme()
init_db()

st.title("📊 Sales Exception Analytics")
st.caption("Trends, volumes, reasons, and notes intelligence — shared read access.")

# ─── Global slicers ──────────────────────────────────────────────────────────
s1, s2, s3 = st.columns([1.2, 1.2, 1.5])
with s1:
    period = st.selectbox(
        "⏱ Time period",
        ["week", "month", "year", "all"],
        index=1,
        format_func=lambda x: {
            "week": "Weekly (last 7 days)",
            "month": "Monthly (last 30 days)",
            "year": "Yearly (last 12 months)",
            "all": "All time",
        }[x],
    )
with s2:
    regions = ["All"] + get_config("regions")
    region = st.selectbox("🗺 Region", regions)
with s3:
    status_focus = st.multiselect(
        "Status focus",
        ["pending", "processing", "audit", "completed", "kicked"],
        default=["pending", "processing", "audit", "completed", "kicked"],
    )

subs = get_submissions_filtered(
    period=period,
    region=None if region == "All" else region,
    limit=5000,
)
if status_focus:
    subs = [s for s in subs if s.get("status") in status_focus]

# KPIs
completed = [s for s in subs if s["status"] == "completed"]
kicked = [s for s in subs if s["status"] == "kicked"]
pending = [s for s in subs if s["status"] == "pending"]
revenue = sum(float(s.get("grand_total") or 0) for s in completed)
avg_ticket = revenue / len(completed) if completed else 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Submissions", len(subs))
k2.metric("Completed", len(completed))
k3.metric("Kicked", len(kicked))
k4.metric("Pending", len(pending))
k5.metric("Completed $", f"${revenue:,.0f}")
k6.metric("Avg ticket", f"${avg_ticket:,.0f}")

st.markdown("---")

# Charts row
c1, c2 = st.columns(2)
with c1:
    st.subheader("Status mix")
    sc = Counter(s["status"] for s in subs)
    if sc:
        df = pd.DataFrame({"status": list(sc.keys()), "count": list(sc.values())})
        fig = px.pie(
            df, names="status", values="count", hole=0.4,
            color="status",
            color_discrete_map={
                "pending": "#ffb74d", "processing": "#64b5f6",
                "audit": "#ba68c8", "completed": "#66bb6a", "kicked": "#e57373",
            },
        )
        fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for this slice.")

with c2:
    st.subheader("Volume trend")
    if subs:
        days = []
        for s in subs:
            d = (s.get("created_at") or "")[:10]
            if d:
                days.append(d)
        if days:
            df = pd.DataFrame(Counter(days).items(), columns=["day", "count"]).sort_values("day")
            fig = px.area(df, x="day", y="count", color_discrete_sequence=["#43a047"])
            fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320,
                              xaxis_title=None, yaxis_title="Submissions")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No dated submissions.")
    else:
        st.info("No data for this slice.")

c3, c4 = st.columns(2)
with c3:
    st.subheader("Exception reasons")
    reasons = Counter(
        (s.get("exception_reason") or "—").strip()
        for s in subs if s.get("exception_reason")
    )
    if reasons:
        df = pd.DataFrame(reasons.most_common(12), columns=["reason", "count"])
        fig = px.bar(df, x="count", y="reason", orientation="h",
                     color_discrete_sequence=["#2e7d32"])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340,
                          yaxis={"categoryorder": "total ascending"},
                          xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No exception reasons in slice.")

with c4:
    st.subheader("Kick reasons")
    kicks = Counter(
        (s.get("kick_reason") or "—").strip()
        for s in kicked if s.get("kick_reason")
    )
    if kicks:
        df = pd.DataFrame(kicks.most_common(12), columns=["reason", "count"])
        fig = px.bar(df, x="count", y="reason", orientation="h",
                     color_discrete_sequence=["#c62828"])
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=340,
                          yaxis={"categoryorder": "total ascending"},
                          xaxis_title=None, yaxis_title=None)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No kicks in this slice.")

c5, c6 = st.columns(2)
with c5:
    st.subheader("Top submitters")
    rep_c = Counter()
    rep_names = {}
    for s in subs:
        eid = s.get("emp_id") or "?"
        rep_c[eid] += 1
        rep_names[eid] = f"{s.get('rep_first', '')} {s.get('rep_last', '')}".strip() or eid
    if rep_c:
        rows = [{"Emp ID": k, "Name": rep_names[k], "Count": v}
                for k, v in rep_c.most_common(12)]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=280)
    else:
        st.info("No submitters.")

with c6:
    st.subheader("Top processors")
    proc = Counter((s.get("admin_user") or "—") for s in subs if s.get("admin_user"))
    if proc:
        df = pd.DataFrame(proc.most_common(12), columns=["Processor", "Count"])
        st.dataframe(df, use_container_width=True, hide_index=True, height=280)
    else:
        st.info("No processors recorded yet.")

# ─── Word cloud / keyword analysis ───────────────────────────────────────────
st.markdown("---")
st.subheader("☁️ Notes intelligence — keywords & commonalities")
st.caption("Derived from sales notes and kick / admin notes in the selected time period.")

STOP = {
    "the", "a", "an", "and", "or", "to", "of", "in", "for", "on", "is", "was", "were",
    "be", "been", "with", "at", "by", "from", "as", "that", "this", "it", "not", "no",
    "are", "but", "if", "they", "their", "has", "have", "had", "will", "can", "we",
    "you", "i", "he", "she", "customer", "sale", "please", "per", "any", "all",
}

def tokenize(text: str) -> list:
    words = re.findall(r"[a-zA-Z']{3,}", (text or "").lower())
    return [w for w in words if w not in STOP]

# Scope notes to filtered submissions
sales_text = " ".join((s.get("sales_notes") or "") for s in subs)
kick_text = " ".join(
    f"{s.get('kick_reason') or ''} {s.get('admin_notes') or ''}"
    for s in subs if s.get("status") == "kicked"
)

wc1, wc2 = st.columns(2)

def render_word_panel(title: str, text: str, color: str):
    tokens = tokenize(text)
    if not tokens:
        st.info(f"No {title.lower()} text in this slice.")
        return
    counts = Counter(tokens).most_common(40)
    # Bar of top terms (always available)
    df = pd.DataFrame(counts[:20], columns=["word", "count"])
    fig = px.bar(df, x="count", y="word", orientation="h",
                 color_discrete_sequence=[color])
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10), height=360,
        yaxis={"categoryorder": "total ascending"},
        xaxis_title=None, yaxis_title=None, title=title,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Optional image word cloud
    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt
        wc = WordCloud(
            width=640, height=320, background_color="white",
            colormap="Greens" if "Sales" in title else "Reds",
            max_words=60, prefer_horizontal=0.85,
        ).generate_from_frequencies(dict(counts))
        fig2, ax = plt.subplots(figsize=(7, 3.2))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig2, use_container_width=True)
        plt.close(fig2)
    except Exception:
        pass

with wc1:
    render_word_panel("Sales entry notes", sales_text, "#2e7d32")
with wc2:
    render_word_panel("Kick & admin notes", kick_text, "#c62828")

# Keyword search
st.markdown("**Keyword search across notes**")
kw = st.text_input("Find submissions containing…", placeholder="e.g. gate, manager, duplicate")
if kw and kw.strip():
    q = kw.strip().lower()
    hits = [
        s for s in subs
        if q in (s.get("sales_notes") or "").lower()
        or q in (s.get("admin_notes") or "").lower()
        or q in (s.get("kick_reason") or "").lower()
        or q in (s.get("exception_reason") or "").lower()
    ]
    st.write(f"**{len(hits)}** hit(s)")
    if hits:
        hdf = pd.DataFrame([
            {
                "ID": s["id"],
                "Status": s["status"],
                "Customer": f"{s.get('cust_last')}, {s.get('cust_first')}",
                "Sales notes": (s.get("sales_notes") or "")[:120],
                "Kick / admin": f"{s.get('kick_reason') or ''} {s.get('admin_notes') or ''}"[:120],
            }
            for s in hits[:100]
        ])
        st.dataframe(hdf, use_container_width=True, hide_index=True)
