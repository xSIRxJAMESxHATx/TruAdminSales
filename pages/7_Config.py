"""
Admin Config – manage lists, tax rates, discounts, admin users.
"""
import streamlit as st
from utils.theme import apply_theme
from utils.db import (
    init_db, verify_admin, get_admin_display, get_config, set_config,
    get_tax_rate, set_tax_rate, get_discounts, add_discount,
    get_archived_services, get_archived_channels, get_patterns,
    get_conn, _hash_pw, _now
)

st.set_page_config(page_title="Config", page_icon="⚙️", layout="wide")
apply_theme()
init_db()

st.title("⚙️ Configuration")

if "admin_user" not in st.session_state:
    st.session_state.admin_user = None

if not st.session_state.admin_user:
    st.subheader("Admin Login")
    u = st.text_input("Username", key="cfg_u")
    p = st.text_input("Password", type="password", key="cfg_p")
    if st.button("Login", key="cfg_login"):
        if verify_admin(u, p):
            st.session_state.admin_user = u
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

st.sidebar.success(f"Logged in as {get_admin_display(st.session_state.admin_user)}")
if st.sidebar.button("Logout", key="cfg_logout"):
    st.session_state.admin_user = None
    st.rerun()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Lists", "Tax Rates", "Discounts", "Archives", "Admin Users"
])

# ─── Lists ───────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Editable Dropdown Lists")
    list_keys = [
        ("exception_reasons", "Exception Reasons"),
        ("kick_reasons", "Kick Reasons"),
        ("regions", "Regions"),
        ("business_units", "Business Units"),
        ("grass_types", "Grass Types"),
        ("programs", "Programs"),
    ]
    for key, label in list_keys:
        with st.expander(label, expanded=False):
            current = get_config(key)
            text = st.text_area(
                f"One item per line – {label}",
                value="\n".join(current),
                key=f"list_{key}",
                height=150
            )
            if st.button(f"Save {label}", key=f"save_{key}"):
                new_vals = [ln.strip() for ln in text.splitlines() if ln.strip()]
                set_config(key, new_vals)
                st.success(f"Saved {len(new_vals)} items for {label}")
                st.rerun()

# ─── Tax ─────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("State Sales Tax Rates")
    st.caption("Used automatically on the sales form based on customer state.")
    state = st.text_input("State (2-letter)", max_chars=2).upper()
    if state:
        current = get_tax_rate(state)
        rate = st.number_input(f"Rate for {state} (e.g. 0.06 = 6%)", min_value=0.0, max_value=0.15,
                               value=float(current), step=0.001, format="%.4f")
        if st.button("Update Tax Rate"):
            set_tax_rate(state, rate)
            st.success(f"{state} set to {rate*100:.2f}%")
    st.markdown("---")
    st.markdown("**Quick view (sample states)**")
    sample = ["TX", "FL", "CA", "NY", "GA", "NC", "OH", "IL"]
    cols = st.columns(4)
    for i, s in enumerate(sample):
        cols[i % 4].metric(s, f"{get_tax_rate(s)*100:.2f}%")

# ─── Discounts ───────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Discount Templates")
    discs = get_discounts()
    if discs:
        st.dataframe(
            [{"Label": d["label"], "Type": d["disc_type"], "Value": d["value"]} for d in discs],
            use_container_width=True, hide_index=True
        )
    st.markdown("**Add new discount**")
    nl = st.text_input("Label")
    nt = st.selectbox("Type", ["percent", "dollar"])
    nv = st.number_input("Value", min_value=0.0, value=0.0)
    if st.button("Add Discount"):
        if nl.strip():
            add_discount(nl.strip(), nt, nv)
            st.success("Added")
            st.rerun()
        else:
            st.error("Label required")

# ─── Archives (read) ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("Archived Services / Channels / Patterns")
    st.markdown("**Lawn services**")
    st.write(", ".join(get_archived_services("lawn")) or "— none yet —")
    st.markdown("**Expanded services**")
    st.write(", ".join(get_archived_services("expanded")) or "— none yet —")
    st.markdown("**Tree & Shrub services**")
    st.write(", ".join(get_archived_services("tree")) or "— none yet —")
    st.markdown("**Sales channels**")
    st.write(", ".join(get_archived_channels()) or "— none yet —")
    st.markdown("**Service patterns**")
    pats = get_patterns()
    if pats:
        st.write(", ".join(f"`{p['pattern']}`" for p in pats))
    else:
        st.write("— none yet —")

# ─── Admin users ─────────────────────────────────────────────────────────────
with tab5:
    st.subheader("Admin Users")
    st.caption("Default admin/admin123 – change password immediately.")
    conn = get_conn()
    users = conn.execute("SELECT username, display_name, created_at FROM admin_users").fetchall()
    conn.close()
    if users:
        st.dataframe(
            [{"Username": u["username"], "Display": u["display_name"], "Created": u["created_at"]} for u in users],
            use_container_width=True, hide_index=True
        )

    st.markdown("**Add / Reset Admin**")
    nu = st.text_input("Username")
    nd = st.text_input("Display name")
    npw = st.text_input("Password", type="password")
    if st.button("Create or Reset Password"):
        if nu and npw:
            conn = get_conn()
            conn.execute(
                """
                INSERT INTO admin_users (username, password_hash, display_name, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    password_hash=excluded.password_hash,
                    display_name=excluded.display_name
                """,
                (nu.strip(), _hash_pw(npw), nd.strip() or nu, _now())
            )
            conn.commit()
            conn.close()
            st.success(f"User '{nu}' saved.")
            st.rerun()
        else:
            st.error("Username and password required")
