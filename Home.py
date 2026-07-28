"""
Lawn Care System Exception Sales Intake
Main landing / navigation page.
"""
import streamlit as st
from utils.theme import apply_theme
from utils.db import init_db, get_notifications

st.set_page_config(
    page_title="Lawn Care Exception Sales",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
init_db()

st.title("🌿 Lawn Care Exception Sales Intake")
st.markdown(
    """
    **System Exception Sales Portal** – for sales that cannot be entered directly into the production system.
    
    Use the sidebar to navigate:
    - **📝 Sales Entry** – Submit a new exception sale
    - **📬 My Submissions** – View your submissions & status notifications
    - **🛠️ Admin Queue** – Process pending / processing sales *(admin only)*
    - **🔍 Audit Queue** – Customer-contact audit workflow *(admin only)*
    - **📦 Kick Archive** – Review rejected sales *(admin only)*
    - **📊 Analytics** – Trends, volumes, reasons *(read-only for sales; full for admin)*
    - **⚙️ Config** – Manage lists, tax rates, discounts, admins *(admin only)*
    """
)

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.info("**Sales Associates**\n\nEnter complete sale details. Required fields must be filled before submit. You will receive in-app notifications when status changes.")
with col2:
    st.success("**Admin Processors**\n\nReview submissions, enter into system or kick with reason. Move complex cases to Audit. Update status – sales rep is notified automatically.")
with col3:
    st.warning("**Security Note**\n\nNever enter payment card numbers, SSNs, or other highly sensitive data in notes. This portal is for operational exception handling only.")

st.markdown(
    """
    <div class="footer-note">
        Light-green lawn-care theme · SQLite persistence · Role-based access via admin password<br>
        Default admin: <code>admin</code> / <code>admin123</code> — change immediately in Config after first login.
    </div>
    """,
    unsafe_allow_html=True,
)
