"""
Lawn Care System Exception Sales — polished landing dashboard.
"""
import streamlit as st
from utils.theme import apply_theme
from utils.db import init_db, get_analytics_data, get_submissions_filtered
from utils.print_form import build_blank_form_pdf

st.set_page_config(
    page_title="Lawn Care Exception Sales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()
init_db()

st.title("🌿 Lawn Care Exception Sales")
st.markdown(
    "Professional portal for **system-exception sales** — intake, processing, audit, archive, and analytics."
)

# Live KPIs
try:
    data = get_analytics_data()
    t = data.get("totals") or {}
    week = get_submissions_filtered(period="week", limit=5000)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("All submissions", int(t.get("total_subs") or 0))
    c2.metric("This week", len(week))
    c3.metric("Pending", int(t.get("pending") or 0))
    c4.metric("In audit", int(t.get("audit") or 0))
    c5.metric("Completed", int(t.get("completed") or 0))
    c6.metric("Volume $", f"${float(t.get('revenue') or 0):,.0f}")
except Exception:
    pass

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    with st.container(border=True):
        st.markdown("#### 📝 Sales team")
        st.markdown(
            """
            - **Sales Entry** — digital intake with live pricing  
            - **My Submissions** — status & notifications  
            - **Submission Archive** — full history over time  
            - **Printable form** — blank PDF for field use  
            """
        )
with col2:
    with st.container(border=True):
        st.markdown("#### 🛠️ Processing")
        st.markdown(
            """
            - **Admin Queue** — process / complete / kick  
            - **Audit Queue** — customer-contact verification  
            - **Kick Archive** — rejected sales history  
            - Processor **name required** for all status changes  
            """
        )
with col3:
    with st.container(border=True):
        st.markdown("#### 📊 Insights")
        st.markdown(
            """
            - Weekly / monthly / yearly **trend slicers**  
            - Region filters & status focus  
            - **Word cloud** on sales & kick notes  
            - Keyword search across notes  
            """
        )

st.markdown("---")
left, right = st.columns([1.4, 1])
with left:
    st.subheader("📄 Printable blank sales form")
    st.caption(
        "One-page professional form for handwritten capture when digital entry isn’t available. "
        "Totals row is compact so every calculation stays visible."
    )
    pdf_bytes = build_blank_form_pdf()
    st.download_button(
        label="⬇️ Download blank Exception Sales form (PDF)",
        data=pdf_bytes,
        file_name="Exception_Sales_Intake_Blank.pdf",
        mime="application/pdf",
        type="primary",
    )
with right:
    st.subheader("📬 Notifications")
    st.markdown(
        """
        Status changes create **in-app** alerts and, when SMTP is configured under 
        **Config → Email**, email the rep address on the sale.
        
        Employee IDs are **normalized** to name, branch, and region for auto-fill on future entries.
        """
    )

st.markdown(
    """
    <div class="footer-note">
        Open team access · Name required for processing · SQLite persistence · Email + in-app notifications<br>
        Never enter payment card numbers or highly sensitive data in notes fields.
    </div>
    """,
    unsafe_allow_html=True,
)
