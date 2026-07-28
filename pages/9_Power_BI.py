"""
Power BI integration — star-schema exports, field catalog, connection guide.
"""
import json
import streamlit as st
import pandas as pd
from utils.theme import apply_theme
from utils.db import init_db, get_submissions, list_employees, get_conn
from utils.schema import (
    SUBMISSION_SCHEMA, SERVICE_LINE_SCHEMA, POWERBI_FIELD_CATALOG,
    schema_as_json_text, STATUS_ENUM,
)

st.set_page_config(page_title="Power BI", page_icon="📈", layout="wide")
apply_theme()
init_db()

st.title("📈 Power BI Integration")
st.caption(
    "Export star-schema datasets, review the refined JSON schema, and connect Power BI Desktop / Service."
)

tab1, tab2, tab3, tab4 = st.tabs([
    "Export datasets", "Field catalog", "JSON schema", "Connection guide"
])

# ─── Build export frames ─────────────────────────────────────────────────────
def build_fact_submissions() -> pd.DataFrame:
    rows = get_submissions(limit=10000)
    if not rows:
        return pd.DataFrame()
    cols = [
        "id", "created_at", "updated_at", "status",
        "cust_first", "cust_last", "cust_phone", "cust_mobile", "cust_email",
        "cust_street", "cust_city", "cust_state", "cust_zip", "property_sqft",
        "grass_type", "emp_id", "rep_first", "rep_last", "rep_email",
        "business_unit", "region", "sales_channel",
        "payment_type", "prepay_pct",
        "subtotal", "total_discount", "total_tax", "grand_total",
        "exception_reason", "sales_notes",
        "admin_user", "admin_notes", "kick_reason", "processed_at",
    ]
    data = []
    for r in rows:
        data.append({c: r.get(c) for c in cols})
    return pd.DataFrame(data)


def build_fact_service_lines() -> pd.DataFrame:
    rows = get_submissions(limit=10000)
    lines = []
    for r in rows:
        try:
            services = json.loads(r.get("services_json") or "[]")
        except Exception:
            services = []
        for i, svc in enumerate(services):
            lines.append({
                "submission_id": r["id"],
                "line_index": i,
                "name": svc.get("name"),
                "service_type": svc.get("service_type"),
                "num_apps": svc.get("num_apps"),
                "price": svc.get("price"),
                "pattern": svc.get("pattern"),
                "line_base": svc.get("line_base"),
                "line_discount": svc.get("line_discount"),
                "line_tax": svc.get("line_tax"),
                "line_total": svc.get("line_total"),
                "status": r.get("status"),
                "region": r.get("region"),
                "created_at": r.get("created_at"),
            })
    return pd.DataFrame(lines)


def build_dim_employee() -> pd.DataFrame:
    emps = list_employees()
    return pd.DataFrame(emps) if emps else pd.DataFrame(
        columns=["emp_id", "rep_first", "rep_last", "rep_email",
                 "business_unit", "region", "branch", "updated_at"]
    )


def build_dim_status() -> pd.DataFrame:
    return pd.DataFrame({
        "status": STATUS_ENUM,
        "sort_order": list(range(1, len(STATUS_ENUM) + 1)),
        "is_terminal": [s in ("completed", "kicked") for s in STATUS_ENUM],
    })


with tab1:
    st.subheader("Star-schema CSV exports for Power BI")
    st.markdown(
        """
        Import these files into **Power BI Desktop** (Get data → Text/CSV), then relate:
        - `fact_service_lines[submission_id]` → `fact_submissions[id]`
        - `fact_submissions[emp_id]` → `dim_employee[emp_id]`
        - `fact_submissions[status]` → `dim_status[status]`
        """
    )
    fact = build_fact_submissions()
    lines = build_fact_service_lines()
    dim_e = build_dim_employee()
    dim_s = build_dim_status()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("fact_submissions", len(fact))
    m2.metric("fact_service_lines", len(lines))
    m3.metric("dim_employee", len(dim_e))
    m4.metric("dim_status", len(dim_s))

    def dl(df: pd.DataFrame, name: str, label: str):
        if df.empty:
            st.caption(f"{label}: no rows yet")
            return
        st.download_button(
            label=f"⬇️ {label}",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=name,
            mime="text/csv",
            key=f"dl_{name}",
        )

    c1, c2 = st.columns(2)
    with c1:
        dl(fact, "fact_submissions.csv", "fact_submissions.csv")
        dl(lines, "fact_service_lines.csv", "fact_service_lines.csv")
    with c2:
        dl(dim_e, "dim_employee.csv", "dim_employee.csv")
        dl(dim_s, "dim_status.csv", "dim_status.csv")

    st.markdown("---")
    st.subheader("Preview — fact_submissions")
    if not fact.empty:
        st.dataframe(fact.head(50), use_container_width=True, hide_index=True)
    else:
        st.info("No submissions yet. Export will populate after the first sale is entered.")

with tab2:
    st.subheader("Power BI field catalog")
    st.dataframe(
        pd.DataFrame(POWERBI_FIELD_CATALOG),
        use_container_width=True,
        hide_index=True,
        height=480,
    )
    cat_csv = pd.DataFrame(POWERBI_FIELD_CATALOG).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ field_catalog.csv", data=cat_csv,
                       file_name="powerbi_field_catalog.csv", mime="text/csv")

with tab3:
    st.subheader("Refined JSON schemas")
    st.markdown(
        """
        Submissions store service lines as **`services_json`** (array of service objects).
        The schemas below document required fields, enums, and bounds used by runtime validation.
        """
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Submission payload**")
        st.json(SUBMISSION_SCHEMA)
    with c2:
        st.markdown("**Service line**")
        st.json(SERVICE_LINE_SCHEMA)

    st.download_button(
        "⬇️ schemas.json",
        data=schema_as_json_text().encode("utf-8"),
        file_name="exception_sales_schemas.json",
        mime="application/json",
    )

with tab4:
    st.subheader("How to connect Power BI")
    st.markdown(
        """
### Option A — CSV refresh (recommended for Streamlit Community Cloud)

1. Open this page and download the four star-schema CSVs.
2. In **Power BI Desktop**: *Get data → Text/CSV* → load each file.
3. **Model view**: create relationships as listed on the Export tab.
4. For refresh: re-download CSVs periodically, or place them on SharePoint / OneDrive  
   and use a scheduled dataflow / gateway.

### Option B — SQLite file (local / self-hosted)

1. Copy `data/sales_intake.db` from the app host.
2. Power BI Desktop → *Get data → SQLite database* (or ODBC).
3. Select tables: `submissions`, `employee_roster`, `audit_log`, etc.
4. In Power Query, expand `services_json` with *Parse JSON* → *Expand to rows*  
   to build a service-line fact table (mirrors `fact_service_lines`).

### Option C — Power BI Service + automation

1. Publish a Desktop report that points at SharePoint-hosted CSVs or a dataflow.
2. Schedule refresh in the Power BI Service.
3. Optional: Azure Function / Logic App that pulls exports on a timer  
   (Streamlit Cloud does not expose a permanent SQL endpoint).

### Suggested measures (DAX)

```dax
Submissions = COUNTROWS(fact_submissions)
Completed $ = CALCULATE(SUM(fact_submissions[grand_total]), fact_submissions[status] = "completed")
Kick Rate % = DIVIDE(
    CALCULATE(COUNTROWS(fact_submissions), fact_submissions[status] = "kicked"),
    COUNTROWS(fact_submissions)
)
Avg Ticket = DIVIDE([Completed $],
    CALCULATE(COUNTROWS(fact_submissions), fact_submissions[status] = "completed"))
```

### Notes

- **Nested JSON**: prefer the exported `fact_service_lines` over parsing JSON in every report.
- **PII**: customer phone/email are included for ops reporting — restrict workspace access.
- **Live DirectQuery** to Streamlit Cloud SQLite is **not** supported; use export or self-host the DB.
        """
    )
