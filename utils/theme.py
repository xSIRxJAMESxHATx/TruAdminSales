"""
Lawn-care themed CSS – light greens, clean professional look.
"""
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Main background */
.stApp {
    background: linear-gradient(180deg, #f0faf0 0%, #e8f5e9 40%, #f5f9f5 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1b5e20 0%, #2e7d32 100%);
}
section[data-testid="stSidebar"] * {
    color: #e8f5e9 !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label {
    color: #c8e6c9 !important;
}

/* Headers */
h1, h2, h3 {
    color: #1b5e20 !important;
}
h1 {
    border-bottom: 3px solid #81c784;
    padding-bottom: 0.3rem;
}

/* Cards / containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid #c8e6c9;
    box-shadow: 0 2px 8px rgba(46, 125, 50, 0.08);
    padding: 1rem;
}

/* Primary buttons */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2e7d32, #43a047);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, #1b5e20, #2e7d32);
    box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3);
}

/* Secondary / default buttons */
.stButton > button {
    border-radius: 8px;
    border: 1px solid #81c784;
    color: #1b5e20;
}

/* Metrics */
div[data-testid="stMetric"] {
    background: #e8f5e9;
    border-radius: 10px;
    padding: 0.8rem;
    border-left: 4px solid #43a047;
}

/* Success / info boxes */
.stSuccess, .stInfo {
    border-radius: 8px;
}

/* Form labels */
label {
    color: #2e7d32 !important;
    font-weight: 500 !important;
}

/* Input focus */
.stTextInput input:focus, .stNumberInput input:focus, .stSelectbox div:focus {
    border-color: #43a047 !important;
    box-shadow: 0 0 0 2px rgba(67, 160, 71, 0.25) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #e8f5e9;
    border-radius: 8px;
    color: #1b5e20 !important;
    font-weight: 600;
}

/* Tables */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}

/* Status badges via markdown */
.badge-pending { background:#fff3e0; color:#e65100; padding:2px 10px; border-radius:12px; font-weight:600; }
.badge-processing { background:#e3f2fd; color:#1565c0; padding:2px 10px; border-radius:12px; font-weight:600; }
.badge-audit { background:#f3e5f5; color:#6a1b9a; padding:2px 10px; border-radius:12px; font-weight:600; }
.badge-completed { background:#e8f5e9; color:#2e7d32; padding:2px 10px; border-radius:12px; font-weight:600; }
.badge-kicked { background:#ffebee; color:#c62828; padding:2px 10px; border-radius:12px; font-weight:600; }

/* Footer note */
.footer-note {
    font-size: 0.85rem;
    color: #558b2f;
    text-align: center;
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid #c8e6c9;
}
</style>
"""

def apply_theme():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
