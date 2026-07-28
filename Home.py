"""
Lawn Care System Exception Sales Intake – professional landing page.
Open access for sales and admin teams (no password gates).
"""
import streamlit as st
from utils.theme import apply_theme
from utils.db import init_db, get_analytics_data
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
    "**System Exception Sales Portal** — capture, route, process, and analyze "
    "sales that cannot be entered directly into the production system."
)

try:
    data = get_analytics_data()
    t = data.get("totals") or {}
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total submissions", int(t.get("total_subs") or 0))
    c2.metric("Pending", int(t.get("pending") or 0))
    c3.metric("In audit", int(t.get("audit") or 0))
    c4.metric("Completed", int(t.get("completed") or 0))
    c5.metric("Volume $", f"${float(t.get('revenue') or 0):,.0f}")
except Exception:
    pass

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("#### 📝 Sales team")
    st.markdown(
        """
        - **Sales Entry** — full digital intake form  
        - **My Submissions** — track status & notifications  
        - **Printable form** — blank PDF for handwritten use  
        - **Analytics** — shared read-only trends  
        """
    )
with col2:
    st.markdown("#### 🛠️ Operations / Admin")
    st.markdown(
        """
        - **Admin Queue** — process pending sales  
        - **Audit Queue** — customer-contact verification  
        - **Kick Archive** — rejected sales history  
        - **Config** — lists, tax rates, discounts, email  
        """
    )
with col3:
    st.markdown("#### 📬 Notifications")
    st.markdown(
        """
        Status changes create **in-app** alerts for the rep  
        and, when SMTP is configured, **email** to the rep’s address.  
        Configure SMTP under **Config → Email**.
        """
    )

st.markdown("---")
st.subheader("📄 Printable blank sales form")
st.caption(
    "Download a clean one-page PDF of the full intake form. "
    "Use when a rep needs to capture the sale on paper and enter later."
)
pdf_bytes = build_blank_form_pdf()
st.download_button(
    label="⬇️ Download blank Exception Sales form (PDF)",
    data=pdf_bytes,
    file_name="Exception_Sales_Intake_Blank.pdf",
    mime="application/pdf",
    type="primary",
)

st.markdown(
    """
    <div class="footer-note">
        Open access for sales &amp; admin · SQLite persistence · Email + in-app notifications<br>
        Never enter payment card numbers or highly sensitive data in notes fields.
    </div>
    """,
    unsafe_allow_html=True,
)
