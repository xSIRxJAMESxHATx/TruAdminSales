# 🌿 Lawn Care System Exception Sales Intake

Professional multi-page **Streamlit** application for capturing, routing, processing, auditing, and analyzing system-exception sales that cannot be entered directly into the production system.

Designed for lawn-care sales teams and admin processors. Ready for GitHub + [Streamlit Community Cloud](https://share.streamlit.io).

---

## Features

### Sales Entry Form (3 sections)
- **Customer** – name, phones, email, full address, property sq ft, areas serviced (F/B/R/L), grass type, special parameters (locked gate, pet, invisible fence, sprinkler).
- **Services**
  - Main Lawn Service – free-text + archive-to-dropdown, # applications, price/app, multi-discount (preset + custom $), auto line pricing, auto sales tax by state, line total.
  - Expanded / Off-template – identical logic.
  - Tree & Shrub – identical + 1–8 round pattern selector → archived as `YNNYYNY`-style codes.
- **Rep / Payment / Notes** – employee ID, name, business unit, region, sales channel (archives), prepay / easypay / invoice, adjustable 5/7/10 % prepay discount, live order totals, exception reason, free-form notes (with sensitivity warning).
- Light-green lawn-care theme, full client-side validation before submit.

### Workflow
1. Sales rep submits → status `pending`.
2. Admin Queue – view full detail, set `processing`, mark `completed`, move to `audit`, or `kick` with reason.
3. Audit Queue – customer-contact workflow → complete or kick.
4. Kick Archive – historical rejected sales (read-only).
5. On every status change the sales rep receives an **in-app notification** (visible on “My Submissions”).

### Analytics
- KPIs, status pie, daily volume, top submitters, top processors, exception-reason & kick-reason breakdowns, recent snapshot table.

### Config (admin only)
- Editable lists: exception reasons, kick reasons, regions, business units, grass types, programs.
- State sales-tax rates (pre-seeded for all US states + DC).
- Discount templates.
- View of all archived services / channels / patterns.
- Create / reset admin users.

### Security & Safety
- Admin pages protected by username/password (SHA-256 hashed).
- Sales team has unrestricted access only to Entry, My Submissions, and Analytics (read-only).
- Default credentials: `admin` / `admin123` – **change immediately**.
- No payment-card or highly sensitive data should be entered (UI warning present).
- SQLite with WAL mode; parameterized queries throughout.

---

## Quick Start (Local)

```bash
# 1. Clone / unzip
cd lawn_sales_app

# 2. Create virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Run
streamlit run Home.py
```

Open http://localhost:8501

---

## Deploy to Streamlit Community Cloud

1. Push this folder to a **public or private** GitHub repository.
2. Go to https://share.streamlit.io → **New app**.
3. Select the repo, branch `main`, Main file path: `Home.py`.
4. Deploy. The SQLite database file lives under `data/` and persists on the Cloud instance (note: free-tier instances may be ephemeral on sleep; for production durability consider connecting an external DB later).
5. (Optional) Add secrets in the Cloud dashboard if you later move admin credentials to `st.secrets`.

---

## Project Layout

```
lawn_sales_app/
├── Home.py                 # Landing / navigation
├── requirements.txt
├── README.md
├── pages/
│   ├── 1_Sales_Entry.py
│   ├── 2_My_Submissions.py
│   ├── 3_Admin_Queue.py
│   ├── 4_Audit_Queue.py
│   ├── 5_Kick_Archive.py
│   ├── 6_Analytics.py
│   └── 7_Config.py
├── utils/
│   ├── db.py               # SQLite schema, CRUD, archives, analytics
│   ├── pricing.py          # Line & order calculations, pattern helper
│   └── theme.py            # Custom CSS (light green lawn theme)
└── data/                   # sales_intake.db created at runtime
```

---

## Default Admin

| Username | Password  |
|----------|-----------|
| admin    | admin123  |

Change via **Config → Admin Users** after first login.

---

## Notes & Limitations

- Sales tax is **state-level** (seeded with approximate statewide rates). City/local add-ons are not modeled; adjust rates in Config as needed or extend `tax_rates` table.
- Notifications are **in-app only** (stored in DB, shown on My Submissions). Email/SMS can be added later via SendGrid, Twilio, etc.
- Concurrent multi-user writes are safe via SQLite WAL; for very high volume migrate to PostgreSQL.
- Streamlit Community Cloud free tier sleeps after inactivity; the DB file is preserved on the instance but cold-starts take a few seconds.

---

## License

Internal use / provided as-is for the requesting organization.
