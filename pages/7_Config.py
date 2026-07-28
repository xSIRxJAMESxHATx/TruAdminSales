"""
Config – lists, tax, discounts, email SMTP. Open access for ops teams.
"""
import streamlit as st
from utils.theme import apply_theme
from utils.db import (
    init_db, get_config, set_config, get_tax_rate, set_tax_rate,
    get_discounts, add_discount, get_archived_services,
    get_archived_channels, get_patterns, list_employees,
)
from utils.email_notify import get_email_settings, save_email_settings

st.set_page_config(page_title="Config", page_icon="⚙️", layout="wide")
apply_theme()
init_db()

st.title("⚙️ Configuration")
st.caption("Manage dropdown lists, tax rates, discounts, and email notifications. Open to sales & admin.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Lists", "Tax Rates", "Discounts", "Email / SMTP", "Archives"
])

with tab1:
    st.subheader("Editable dropdown lists")
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
            # skip non-list email_settings style
            if current and isinstance(current[0], str) and current[0].startswith("{"):
                continue
            text = st.text_area(
                f"One item per line — {label}",
                value="\n".join(current) if isinstance(current, list) else "",
                key=f"list_{key}",
                height=140,
            )
            if st.button(f"Save {label}", key=f"save_{key}"):
                new_vals = [ln.strip() for ln in text.splitlines() if ln.strip()]
                set_config(key, new_vals)
                st.success(f"Saved {len(new_vals)} items")
                st.rerun()

with tab2:
    st.subheader("State sales tax rates")
    st.caption("Applied automatically on the sales form from the customer’s state.")
    state = st.text_input("State (2-letter)", max_chars=2).upper()
    if state:
        current = get_tax_rate(state)
        rate = st.number_input(
            f"Rate for {state} (e.g. 0.06 = 6%)",
            min_value=0.0, max_value=0.15, value=float(current),
            step=0.001, format="%.4f",
        )
        if st.button("Update tax rate"):
            set_tax_rate(state, rate)
            st.success(f"{state} → {rate*100:.2f}%")
    st.markdown("---")
    sample = ["TX", "FL", "CA", "NY", "GA", "NC", "OH", "IL"]
    cols = st.columns(4)
    for i, s in enumerate(sample):
        cols[i % 4].metric(s, f"{get_tax_rate(s)*100:.2f}%")

with tab3:
    st.subheader("Discount templates")
    discs = get_discounts()
    if discs:
        st.dataframe(
            [{"Label": d["label"], "Type": d["disc_type"], "Value": d["value"]} for d in discs],
            use_container_width=True, hide_index=True,
        )
    st.markdown("**Add discount**")
    nl = st.text_input("Label")
    nt = st.selectbox("Type", ["percent", "dollar"])
    nv = st.number_input("Value", min_value=0.0, value=0.0)
    if st.button("Add discount"):
        if nl.strip():
            add_discount(nl.strip(), nt, nv)
            st.success("Added")
            st.rerun()
        else:
            st.error("Label required")

with tab4:
    st.subheader("Email notifications (SMTP)")
    st.markdown(
        "When enabled, status changes email the **rep email** captured on the sales form. "
        "In-app notifications always work regardless of SMTP."
    )
    settings = get_email_settings()
    enabled = st.checkbox("Enable email notifications", value=bool(settings.get("enabled")))
    host = st.text_input("SMTP host", value=settings.get("smtp_host") or "", placeholder="smtp.office365.com")
    port = st.number_input("SMTP port", value=int(settings.get("smtp_port") or 587), min_value=1, max_value=65535)
    user = st.text_input("SMTP username", value=settings.get("smtp_user") or "")
    password = st.text_input("SMTP password / app password", value=settings.get("smtp_pass") or "", type="password")
    from_email = st.text_input("From address", value=settings.get("from_email") or "", placeholder="noreply@yourcompany.com")
    use_tls = st.checkbox("Use STARTTLS", value=settings.get("use_tls", True))

    if st.button("Save email settings", type="primary"):
        save_email_settings({
            "enabled": enabled,
            "smtp_host": host.strip(),
            "smtp_port": int(port),
            "smtp_user": user.strip(),
            "smtp_pass": password,
            "from_email": from_email.strip(),
            "use_tls": use_tls,
        })
        st.success("Email settings saved.")
        st.rerun()

    st.caption(
        "Tip: For Gmail/Google Workspace use an App Password. "
        "For Microsoft 365 use smtp.office365.com port 587 with STARTTLS."
    )

with tab5:
    st.subheader("Archived services · channels · patterns")
    st.markdown("**Lawn**")
    st.write(", ".join(get_archived_services("lawn")) or "— none yet —")
    st.markdown("**Expanded**")
    st.write(", ".join(get_archived_services("expanded")) or "— none yet —")
    st.markdown("**Tree & Shrub**")
    st.write(", ".join(get_archived_services("tree")) or "— none yet —")
    st.markdown("**Sales channels**")
    st.write(", ".join(get_archived_channels()) or "— none yet —")
    pats = get_patterns()
    st.markdown("**Patterns**")
    st.write(", ".join(f"`{p['pattern']}`" for p in pats) if pats else "— none yet —")
    st.markdown("---")
    st.markdown("**Employee roster (normalized emp ID → name / region / branch)**")
    emps = list_employees()
    if emps:
        import pandas as pd
        st.dataframe(pd.DataFrame(emps), use_container_width=True, hide_index=True)
    else:
        st.write("— none yet — (populated automatically when sales are submitted)")
