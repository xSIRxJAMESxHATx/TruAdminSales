"""
Professional lawn-care sales theme – refined layout, cards, badges, polish.
"""
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', system-ui, sans-serif;
}

.stApp {
    background: linear-gradient(165deg, #f3faf3 0%, #eef7ee 45%, #f7fbf7 100%);
}

section[data-testid="stSidebar"] {
    background: linear-gradient(185deg, #1b5e20 0%, #2e7d32 55%, #388e3c 100%);
    border-right: 1px solid #145a1a;
}
section[data-testid="stSidebar"] * {
    color: #e8f5e9 !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] p {
    color: #c8e6c9 !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    border-radius: 8px;
    margin: 2px 0;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.12);
}

h1 {
    color: #1b5e20 !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
    border-bottom: 3px solid #81c784;
    padding-bottom: 0.35rem;
    margin-bottom: 0.75rem;
}
h2, h3 {
    color: #2e7d32 !important;
    font-weight: 600 !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff;
    border-radius: 14px;
    border: 1px solid #c8e6c9;
    box-shadow: 0 2px 10px rgba(46, 125, 50, 0.07);
    padding: 0.85rem 1rem;
    margin-bottom: 0.5rem;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #2e7d32, #43a047) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.4rem !important;
    box-shadow: 0 2px 6px rgba(46,125,50,0.25);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, #1b5e20, #2e7d32) !important;
    box-shadow: 0 4px 14px rgba(46, 125, 50, 0.35);
}
.stButton > button {
    border-radius: 10px !important;
    border: 1px solid #81c784 !important;
    color: #1b5e20 !important;
    font-weight: 500 !important;
}

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #e8f5e9, #f1f8e9);
    border-radius: 12px;
    padding: 0.75rem 0.9rem;
    border-left: 4px solid #43a047;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
div[data-testid="stMetric"] label {
    color: #558b2f !important;
    font-weight: 500 !important;
}

label {
    color: #2e7d32 !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

.streamlit-expanderHeader {
    background: #e8f5e9 !important;
    border-radius: 10px !important;
    color: #1b5e20 !important;
    font-weight: 600 !important;
}

.badge-pending { background:#fff3e0; color:#e65100; padding:3px 12px; border-radius:14px; font-weight:600; font-size:0.85rem; }
.badge-processing { background:#e3f2fd; color:#1565c0; padding:3px 12px; border-radius:14px; font-weight:600; font-size:0.85rem; }
.badge-audit { background:#f3e5f5; color:#6a1b9a; padding:3px 12px; border-radius:14px; font-weight:600; font-size:0.85rem; }
.badge-completed { background:#e8f5e9; color:#2e7d32; padding:3px 12px; border-radius:14px; font-weight:600; font-size:0.85rem; }
.badge-kicked { background:#ffebee; color:#c62828; padding:3px 12px; border-radius:14px; font-weight:600; font-size:0.85rem; }

.footer-note {
    font-size: 0.82rem;
    color: #558b2f;
    text-align: center;
    margin-top: 2rem;
    padding: 1rem;
    border-top: 1px solid #c8e6c9;
}

.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1200px;
}
</style>
"""

def apply_theme():
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
