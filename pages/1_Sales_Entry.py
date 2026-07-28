"""
Sales Entry Form – full three-section intake for system exception sales.
"""
import streamlit as st
import json
from utils.theme import apply_theme
from utils.db import (
    init_db, archive_service, get_archived_services,
    archive_channel, get_archived_channels, get_discounts,
    archive_pattern, create_submission, get_config, get_tax_rate
)
from utils.pricing import calc_service_line, calc_order_totals, pattern_from_selection
from utils.print_form import build_blank_form_pdf

st.set_page_config(page_title="Sales Entry", page_icon="📝", layout="wide")
apply_theme()
init_db()

st.title("📝 Exception Sales Entry Form")
st.caption("Complete all required fields. Pricing, tax, and totals calculate automatically.")

with st.sidebar:
    st.markdown("### 📄 Paper form")
    st.caption("Need to capture offline? Download a blank printable form.")
    st.download_button(
        "⬇️ Blank form PDF",
        data=build_blank_form_pdf(),
        file_name="Exception_Sales_Intake_Blank.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

# ─── Session state for dynamic service rows ───────────────────────────────────
if "lawn_services" not in st.session_state:
    st.session_state.lawn_services = [{"name": "", "num_apps": 1, "price": 0.0, "discounts": []}]
if "expanded_services" not in st.session_state:
    st.session_state.expanded_services = []
if "tree_services" not in st.session_state:
    st.session_state.tree_services = []

# ─── TOP THIRD: Customer ─────────────────────────────────────────────────────
st.header("① Customer Information")
with st.container(border=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        cust_first = st.text_input("First Name *", key="cust_first")
        cust_phone = st.text_input("Phone Number *", key="cust_phone")
        cust_email = st.text_input("Email Address", key="cust_email")
        cust_city = st.text_input("City *", key="cust_city")
        property_sqft = st.number_input("Property Sq Ft", min_value=0, value=0, step=100, key="sqft")
    with c2:
        cust_last = st.text_input("Last Name *", key="cust_last")
        cust_mobile = st.text_input("Mobile / Alt Number", key="cust_mobile")
        cust_street = st.text_input("Street Address *", key="cust_street")
        cust_state = st.text_input("State * (2-letter)", max_chars=2, key="cust_state").upper()
        grass_types = get_config("grass_types")
        grass_type = st.selectbox("Grass Type", options=[""] + grass_types, key="grass")
    with c3:
        cust_zip = st.text_input("ZIP Code *", key="cust_zip")
        st.markdown("**Areas Being Serviced**")
        areas = []
        a1, a2 = st.columns(2)
        with a1:
            if st.checkbox("Front", key="area_front"): areas.append("Front")
            if st.checkbox("Back", key="area_back"): areas.append("Back")
        with a2:
            if st.checkbox("Right", key="area_right"): areas.append("Right")
            if st.checkbox("Left", key="area_left"): areas.append("Left")
        st.markdown("**Special Service Parameters**")
        special = []
        s1, s2 = st.columns(2)
        with s1:
            if st.checkbox("Locked Gate", key="sp_gate"): special.append("Locked Gate")
            if st.checkbox("Pet on property", key="sp_pet"): special.append("Pet")
        with s2:
            if st.checkbox("Invisible Fence", key="sp_fence"): special.append("Invisible Fence")
            if st.checkbox("Sprinkler System", key="sp_sprinkler"): special.append("Sprinkler System")

# ─── MIDDLE THIRD: Services ──────────────────────────────────────────────────
st.header("② Services")

discount_opts = get_discounts()
discount_labels = [d["label"] for d in discount_opts]
tax_rate = get_tax_rate(cust_state) if cust_state else 0.0
st.caption(f"Current sales-tax rate for state **{cust_state or '—'}**: **{tax_rate*100:.2f}%** (auto-applied)")

def render_service_block(prefix: str, service_type: str, rows_key: str, show_pattern: bool = False):
    """Reusable service entry block (lawn / expanded / tree)."""
    archived = get_archived_services(service_type)
    st.subheader(prefix)

    for idx, row in enumerate(st.session_state[rows_key]):
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 2, 1.5, 1.2, 1.2, 0.5])
            with cols[0]:
                # Name: free text + archive
                name_choice = st.selectbox(
                    "Service Name",
                    options=["— type new —"] + archived,
                    key=f"{rows_key}_sel_{idx}",
                    index=0 if not row.get("name") else (archived.index(row["name"]) + 1 if row["name"] in archived else 0)
                )
                if name_choice == "— type new —":
                    name = st.text_input("New service name", value=row.get("name", ""), key=f"{rows_key}_name_{idx}")
                else:
                    name = name_choice
                    st.text_input("Selected", value=name, disabled=True, key=f"{rows_key}_name_disp_{idx}")
                row["name"] = name

            with cols[1]:
                row["num_apps"] = st.number_input("# Apps", min_value=1, max_value=24, value=row.get("num_apps", 1), key=f"{rows_key}_apps_{idx}")
            with cols[2]:
                row["price"] = st.number_input("Price / App $", min_value=0.0, value=float(row.get("price", 0)), step=5.0, key=f"{rows_key}_price_{idx}")

            with cols[3]:
                selected_discs = st.multiselect(
                    "Discounts",
                    options=discount_labels,
                    default=row.get("disc_labels", []),
                    key=f"{rows_key}_disc_{idx}"
                )
                row["disc_labels"] = selected_discs
                # Resolve full discount objects
                row["discounts"] = [d for d in discount_opts if d["label"] in selected_discs]
                # Custom $ discount
                custom_dollar = st.number_input("Extra $ off", min_value=0.0, value=0.0, step=1.0, key=f"{rows_key}_cd_{idx}")
                if custom_dollar > 0:
                    row["discounts"].append({"label": "Custom $", "type": "dollar", "value": custom_dollar})

            # Calculate line
            is_laf = any("last app free" in (d.get("label") or "").lower() for d in row.get("discounts", []))
            line = calc_service_line(
                row.get("price", 0),
                row.get("num_apps", 1),
                [{"type": d.get("disc_type", d.get("type", "percent")), "value": d.get("value", 0), "label": d.get("label", "")}
                 for d in row.get("discounts", [])],
                tax_rate,
                is_last_app_free=is_laf,
            )
            row["line_base"] = line["base"]
            row["line_discount"] = line["discount"]
            row["line_tax"] = line["tax"]
            row["line_total"] = line["total"]
            row["service_type"] = service_type

            with cols[4]:
                st.metric("After Disc", f"${line['after_discount']:.2f}")
            with cols[5]:
                st.metric("Tax", f"${line['tax']:.2f}")
            with cols[6]:
                st.metric("Line Total", f"${line['total']:.2f}")
            with cols[7]:
                if st.button("🗑", key=f"{rows_key}_del_{idx}"):
                    st.session_state[rows_key].pop(idx)
                    st.rerun()

            # Tree/Shrub pattern
            if show_pattern:
                st.markdown("**Service Pattern (select rounds 1–8 that will be performed)**")
                pcols = st.columns(8)
                selected_rounds = []
                for r in range(1, 9):
                    with pcols[r - 1]:
                        if st.checkbox(str(r), key=f"{rows_key}_pat_{idx}_{r}", value=r in row.get("rounds", [])):
                            selected_rounds.append(r)
                pattern = pattern_from_selection(selected_rounds)
                row["pattern"] = pattern
                row["rounds"] = selected_rounds
                st.caption(f"Pattern code: `{pattern}` (will be archived)")

    if st.button(f"➕ Add {prefix} line", key=f"add_{rows_key}"):
        st.session_state[rows_key].append({"name": "", "num_apps": 1, "price": 0.0, "discounts": []})
        st.rerun()

# Main Lawn
render_service_block("Main Lawn Service", "lawn", "lawn_services")

# Expanded / Off-template
with st.expander("Expanded / Off-Template Services", expanded=bool(st.session_state.expanded_services)):
    render_service_block("Expanded / Other Service", "expanded", "expanded_services")

# Tree & Shrub
with st.expander("Tree & Shrub Care", expanded=bool(st.session_state.tree_services)):
    render_service_block("Tree & Shrub Service", "tree", "tree_services", show_pattern=True)

# Collect all services
all_services = (
    [s for s in st.session_state.lawn_services if s.get("name")]
    + [s for s in st.session_state.expanded_services if s.get("name")]
    + [s for s in st.session_state.tree_services if s.get("name")]
)

# ─── BOTTOM THIRD: Rep / Payment / Notes ─────────────────────────────────────
st.header("③ Sales Rep, Payment & Submission")
with st.container(border=True):
    r1, r2, r3 = st.columns(3)
    with r1:
        emp_id = st.text_input("Employee ID *", key="emp_id")
        rep_first = st.text_input("Rep First Name *", key="rep_first")
        rep_last = st.text_input("Rep Last Name *", key="rep_last")
        rep_email = st.text_input("Rep Email (for status notifications)", key="rep_email", placeholder="you@company.com")
    with r2:
        bus_units = get_config("business_units")
        business_unit = st.selectbox("Business Unit *", options=[""] + bus_units, key="bu")
        regions = get_config("regions")
        region = st.selectbox("Region *", options=[""] + regions, key="region")
        channels = get_archived_channels()
        ch_choice = st.selectbox("Sales Channel", options=["— type new —"] + channels, key="ch_sel")
        if ch_choice == "— type new —":
            sales_channel = st.text_input("New channel name", key="ch_new")
        else:
            sales_channel = ch_choice
    with r3:
        st.markdown("**Payment Type ***")
        pay_prepay = st.checkbox("Prepay", key="pay_prepay")
        pay_easpay = st.checkbox("Easypay", key="pay_easpay")
        pay_invoice = st.checkbox("Invoice", key="pay_invoice")
        prepay_pct = 0.0
        if pay_prepay:
            prepay_pct = st.selectbox("Prepay Discount %", options=[5, 7, 10], key="prepay_pct")
        payment_type = "prepay" if pay_prepay else ("easpay" if pay_easpay else ("invoice" if pay_invoice else ""))

# Totals
order = calc_order_totals(all_services, cust_state, prepay_pct if pay_prepay else 0)
t1, t2, t3, t4 = st.columns(4)
t1.metric("Subtotal (pre-disc)", f"${order['subtotal']:.2f}")
t2.metric("Total Discount", f"${order['total_discount']:.2f}")
t3.metric("Total Sales Tax", f"${order['total_tax']:.2f}")
t4.metric("Grand Total (customer pays)", f"${order['grand_total']:.2f}")

reasons = get_config("exception_reasons")
exception_reason = st.selectbox("Reason for System Exception Sale *", options=[""] + reasons, key="ex_reason")
sales_notes = st.text_area(
    "Notes / Special Instructions",
    height=120,
    placeholder="Special service instructions, manager approval notes, etc. DO NOT enter sensitive payment or personal data here.",
    key="sales_notes"
)
st.caption("⚠️ Do not send any sensitive customer or payment information on this form.")

# ─── Validation & Submit ─────────────────────────────────────────────────────
def validate() -> list:
    errs = []
    if not cust_first.strip(): errs.append("Customer first name required")
    if not cust_last.strip(): errs.append("Customer last name required")
    if not cust_phone.strip(): errs.append("Phone number required")
    if not cust_street.strip(): errs.append("Street address required")
    if not cust_city.strip(): errs.append("City required")
    if not cust_state or len(cust_state) != 2: errs.append("Valid 2-letter state required")
    if not cust_zip.strip(): errs.append("ZIP required")
    if not emp_id.strip(): errs.append("Employee ID required")
    if not rep_first.strip() or not rep_last.strip(): errs.append("Rep name required")
    if not business_unit: errs.append("Business unit required")
    if not region: errs.append("Region required")
    if not payment_type: errs.append("Select a payment type")
    if not exception_reason: errs.append("Exception reason required")
    if not all_services: errs.append("At least one service with a name is required")
    for s in all_services:
        if s.get("price", 0) <= 0:
            errs.append(f"Service '{s.get('name')}' needs a price > 0")
    return errs

if st.button("🚀 Submit Exception Sale", type="primary", use_container_width=True):
    errors = validate()
    if errors:
        for e in errors:
            st.error(e)
    else:
        # Archive new items
        for s in all_services:
            archive_service(s["name"], s["service_type"])
            if s.get("pattern"):
                archive_pattern(s["pattern"])
        if sales_channel:
            archive_channel(sales_channel)

        payload = {
            "cust_first": cust_first.strip(),
            "cust_last": cust_last.strip(),
            "cust_phone": cust_phone.strip(),
            "cust_mobile": cust_mobile.strip(),
            "cust_email": cust_email.strip(),
            "cust_street": cust_street.strip(),
            "cust_city": cust_city.strip(),
            "cust_state": cust_state,
            "cust_zip": cust_zip.strip(),
            "property_sqft": property_sqft,
            "areas_serviced": areas,
            "grass_type": grass_type,
            "special_params": special,
            "services": all_services,
            "emp_id": emp_id.strip(),
            "rep_first": rep_first.strip(),
            "rep_last": rep_last.strip(),
            "rep_email": (rep_email or "").strip(),
            "business_unit": business_unit,
            "region": region,
            "sales_channel": sales_channel.strip() if sales_channel else "",
            "payment_type": payment_type,
            "prepay_pct": prepay_pct if pay_prepay else 0,
            "subtotal": order["subtotal"],
            "total_discount": order["total_discount"],
            "total_tax": order["total_tax"],
            "grand_total": order["grand_total"],
            "exception_reason": exception_reason,
            "sales_notes": sales_notes.strip(),
        }
        try:
            sid = create_submission(payload)
            st.success(f"✅ Sale submitted successfully! Submission ID: **{sid}**. Status: pending. You will be notified when it is processed.")
            st.balloons()
            # Clear dynamic rows
            st.session_state.lawn_services = [{"name": "", "num_apps": 1, "price": 0.0, "discounts": []}]
            st.session_state.expanded_services = []
            st.session_state.tree_services = []
        except Exception as ex:
            st.error(f"Submission failed: {ex}")
