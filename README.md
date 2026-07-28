# 🌿 Lawn Care System Exception Sales Intake

Professional multi-page **Streamlit** app for capturing, routing, processing, auditing, and analyzing system-exception sales.

**Open access** — sales and admin teams can use every page (no password gates). Optional name/ID on admin pages for the audit trail.

Ready for GitHub + [Streamlit Community Cloud](https://share.streamlit.io).

---

## Features

### Sales Entry
- Full customer block, multi-service lines (lawn / expanded / tree+pattern), discounts, auto state tax, prepay %, order totals
- Service names, channels, and tree patterns **archive** for future dropdowns
- **Rep email** for status notifications
- **Download blank PDF form** (sidebar + Home) for handwritten capture

### Workflow
`pending` → Admin Queue (`processing` / `completed` / `audit` / `kick`) → Audit Queue → Kick Archive  

Status changes create **in-app notifications** and, when SMTP is configured, **email** to the rep.

### Analytics
KPIs, status distribution, daily volume, top submitters/processors, exception & kick reasons.

### Config
- Dropdown lists (reasons, regions, BUs, grass types, …)
- State tax rates
- Discount templates
- **Email / SMTP** settings
- Archive viewer

### Printable form
One-page professional PDF of the full intake form — fill by pen when digital entry isn’t available.

---

## Quick start (local)

```bash
cd lawn_sales_app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run Home.py
```

## Deploy to Streamlit Community Cloud

1. Push this folder to GitHub.
2. [share.streamlit.io](https://share.streamlit.io) → New app → Main file: `Home.py`.
3. Under **Config → Email / SMTP**, add your company SMTP (optional but recommended).

---

## Email notifications

Configure under **Config → Email / SMTP**:

| Field | Example |
|-------|---------|
| Host | `smtp.office365.com` or `smtp.gmail.com` |
| Port | `587` |
| TLS | On (STARTTLS) |
| User / password | Mailbox or app password |
| From | `noreply@yourcompany.com` |

Enable the checkbox. Status changes will email the **Rep Email** from the sales form. In-app notifications always work.

---

## Project layout

```
Home.py
pages/
  1_Sales_Entry.py
  2_My_Submissions.py
  3_Admin_Queue.py
  4_Audit_Queue.py
  5_Kick_Archive.py
  6_Analytics.py
  7_Config.py
utils/
  db.py  pricing.py  theme.py  email_notify.py  print_form.py
data/          # SQLite created at runtime
requirements.txt
```

---

## Notes

- Open access by design (per request). Optionally restrict via Streamlit Cloud sharing / SSO later.
- Sales tax is **state-level** (seeded US rates); adjust in Config.
- Never put card numbers or highly sensitive data in notes.
- SQLite is fine for typical team volume; migrate to Postgres for very high concurrency.

