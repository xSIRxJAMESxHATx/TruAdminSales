"""
SQLite persistence layer for Lawn Care Exception Sales Intake App.
All tables, migrations, helpers, and safe queries live here.
"""
import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
# validation imported lazily in create_submission
import hashlib

# Persistent path – works both locally and on Streamlit Cloud
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "sales_intake.db"

# ─── Connection helper ───────────────────────────────────────────────────────
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Avoid WAL on some restricted filesystems; DELETE mode is safer for Cloud
    try:
        conn.execute("PRAGMA journal_mode = DELETE")
    except Exception:
        pass
    return conn

# ─── Schema ──────────────────────────────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS submissions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending | processing | audit | completed | kicked
    -- Customer
    cust_first      TEXT,
    cust_last       TEXT,
    cust_phone      TEXT,
    cust_mobile     TEXT,
    cust_email      TEXT,
    cust_street     TEXT,
    cust_city       TEXT,
    cust_state      TEXT,
    cust_zip        TEXT,
    property_sqft   REAL,
    areas_serviced  TEXT,          -- JSON list
    grass_type      TEXT,
    special_params  TEXT,          -- JSON list of locked_gate, pet, invisible_fence, sprinkler
    -- Services (JSON array of service objects)
    services_json   TEXT NOT NULL DEFAULT '[]',
    -- Rep
    emp_id          TEXT,
    rep_first       TEXT,
    rep_last        TEXT,
    business_unit   TEXT,
    region          TEXT,
    sales_channel   TEXT,
    -- Payment
    payment_type    TEXT,          -- prepay | easpay | invoice
    prepay_pct      REAL DEFAULT 0,
    -- Totals (denormalized for analytics)
    subtotal        REAL DEFAULT 0,
    total_discount  REAL DEFAULT 0,
    total_tax       REAL DEFAULT 0,
    grand_total     REAL DEFAULT 0,
    -- Exception reason & notes
    exception_reason TEXT,
    sales_notes     TEXT,
    -- Admin workflow
    admin_user      TEXT,
    admin_notes     TEXT,
    kick_reason     TEXT,
    processed_at    TEXT,
    -- Notification flag for sales rep
    notified        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS service_archive (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    service_type TEXT NOT NULL,   -- lawn | expanded | tree
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS channel_archive (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS discount_archive (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    label       TEXT NOT NULL UNIQUE,
    disc_type   TEXT NOT NULL,    -- percent | dollar
    value       REAL NOT NULL,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS pattern_archive (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern     TEXT NOT NULL UNIQUE,  -- e.g. YNNYYNY
    label       TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS config_lists (
    key         TEXT PRIMARY KEY,      -- reasons, regions, branches, programs, grass_types, kick_reasons, audit_reasons
    value_json  TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS tax_rates (
    state       TEXT PRIMARY KEY,
    rate        REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS admin_users (
    username    TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    emp_id      TEXT NOT NULL,
    submission_id INTEGER,
    message     TEXT,
    created_at  TEXT,
    read_flag   INTEGER DEFAULT 0,
    FOREIGN KEY (submission_id) REFERENCES submissions(id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER,
    action      TEXT,
    actor       TEXT,
    details     TEXT,
    created_at  TEXT
);

"""

DEFAULT_CONFIGS = {
    "exception_reasons": [
        "System downtime",
        "New product not yet in system",
        "Special pricing override",
        "Customer account issue",
        "Multi-property bundle",
        "Contract exception",
        "Other"
    ],
    "kick_reasons": [
        "Incomplete customer info",
        "Pricing error",
        "Duplicate submission",
        "Unauthorized discount",
        "Missing manager approval",
        "Invalid service combination",
        "Other"
    ],
    "regions": ["Northeast", "Southeast", "Midwest", "Southwest", "West", "Central"],
    "business_units": ["Residential", "Commercial", "HOA", "Municipal"],
    "grass_types": ["Bermuda", "Fescue", "Kentucky Bluegrass", "Zoysia", "St. Augustine", "Ryegrass", "Mixed", "Other"],
    "programs": ["Core Lawn", "Premium Lawn", "Tree & Shrub", "Mosquito", "Aeration", "Overseed", "Custom"],
}

DEFAULT_TAX = {
    "AL": 0.04, "AK": 0.00, "AZ": 0.056, "AR": 0.065, "CA": 0.0725,
    "CO": 0.029, "CT": 0.0635, "DE": 0.00, "FL": 0.06, "GA": 0.04,
    "HI": 0.04, "ID": 0.06, "IL": 0.0625, "IN": 0.07, "IA": 0.06,
    "KS": 0.065, "KY": 0.06, "LA": 0.0445, "ME": 0.055, "MD": 0.06,
    "MA": 0.0625, "MI": 0.06, "MN": 0.06875, "MS": 0.07, "MO": 0.04225,
    "MT": 0.00, "NE": 0.055, "NV": 0.0685, "NH": 0.00, "NJ": 0.06625,
    "NM": 0.05125, "NY": 0.04, "NC": 0.0475, "ND": 0.05, "OH": 0.0575,
    "OK": 0.045, "OR": 0.00, "PA": 0.06, "RI": 0.07, "SC": 0.06,
    "SD": 0.045, "TN": 0.07, "TX": 0.0625, "UT": 0.061, "VT": 0.06,
    "VA": 0.053, "WA": 0.065, "WV": 0.06, "WI": 0.05, "WY": 0.04,
    "DC": 0.06
}

DEFAULT_DISCOUNTS = [
    ("20% off all applications", "percent", 20),
    ("50% off first service", "percent", 50),
    ("50% off last service", "percent", 50),
    ("Last app free", "percent", 100),  # special handling later
    ("Military discount", "percent", 10),
    ("Senior citizen discount", "percent", 10),
    ("Price match", "dollar", 0),
    ("Off template", "percent", 0),
]

def init_db():
    """Create tables and seed defaults if empty. Robust against restricted FS."""
    import time
    tables_sql = [
        """CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            cust_first TEXT, cust_last TEXT, cust_phone TEXT, cust_mobile TEXT, cust_email TEXT,
            cust_street TEXT, cust_city TEXT, cust_state TEXT, cust_zip TEXT,
            property_sqft REAL, areas_serviced TEXT, grass_type TEXT, special_params TEXT,
            services_json TEXT NOT NULL DEFAULT '[]',
            emp_id TEXT, rep_first TEXT, rep_last TEXT, rep_email TEXT,
            business_unit TEXT, region TEXT, sales_channel TEXT,
            payment_type TEXT, prepay_pct REAL DEFAULT 0,
            subtotal REAL DEFAULT 0, total_discount REAL DEFAULT 0, total_tax REAL DEFAULT 0, grand_total REAL DEFAULT 0,
            exception_reason TEXT, sales_notes TEXT,
            admin_user TEXT, admin_notes TEXT, kick_reason TEXT, processed_at TEXT, notified INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS service_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
            service_type TEXT NOT NULL, created_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS channel_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, created_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS discount_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT NOT NULL UNIQUE,
            disc_type TEXT NOT NULL, value REAL NOT NULL, created_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS pattern_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT, pattern TEXT NOT NULL UNIQUE,
            label TEXT, created_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS config_lists (
            key TEXT PRIMARY KEY, value_json TEXT NOT NULL DEFAULT '[]'
        )""",
        """CREATE TABLE IF NOT EXISTS tax_rates (
            state TEXT PRIMARY KEY, rate REAL NOT NULL DEFAULT 0.0
        )""",
        """CREATE TABLE IF NOT EXISTS admin_users (
            username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
            display_name TEXT, created_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, emp_id TEXT NOT NULL,
            submission_id INTEGER, message TEXT, created_at TEXT, read_flag INTEGER DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS processor_roster (
            name TEXT PRIMARY KEY,
            display_name TEXT,
            updated_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS employee_roster (
            emp_id TEXT PRIMARY KEY,
            rep_first TEXT, rep_last TEXT, rep_email TEXT,
            business_unit TEXT, region TEXT, branch TEXT,
            updated_at TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, submission_id INTEGER,
            action TEXT, actor TEXT, details TEXT, created_at TEXT
        )""",
    ]
    for sql in tables_sql:
        for attempt in range(3):
            try:
                conn = get_conn()
                conn.execute(sql)
                conn.commit()
                conn.close()
                break
            except sqlite3.OperationalError as e:
                if attempt == 2:
                    # Last attempt – ignore only if table somehow exists
                    try:
                        conn = get_conn()
                        conn.execute(sql)
                        conn.commit()
                        conn.close()
                    except Exception:
                        pass
                else:
                    time.sleep(0.15)

    # Lightweight migrations for columns added after first release
    conn = get_conn()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(submissions)").fetchall()]
        if "rep_email" not in cols:
            conn.execute("ALTER TABLE submissions ADD COLUMN rep_email TEXT")
            conn.commit()
    except Exception:
        pass
    conn.close()

    conn = get_conn()
    # Seed config lists
    for key, vals in DEFAULT_CONFIGS.items():
        cur = conn.execute("SELECT 1 FROM config_lists WHERE key=?", (key,))
        if not cur.fetchone():
            conn.execute(
                "INSERT INTO config_lists (key, value_json) VALUES (?, ?)",
                (key, json.dumps(vals))
            )
    # Seed tax rates
    for state, rate in DEFAULT_TAX.items():
        conn.execute(
            "INSERT OR IGNORE INTO tax_rates (state, rate) VALUES (?, ?)",
            (state, rate)
        )
    # Seed default discounts
    for label, dtype, val in DEFAULT_DISCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO discount_archive (label, disc_type, value, created_at) VALUES (?, ?, ?, ?)",
            (label, dtype, val, _now())
        )
    # Default admin
    cur = conn.execute("SELECT 1 FROM admin_users WHERE username='admin'")
    if not cur.fetchone():
        conn.execute(
            "INSERT INTO admin_users (username, password_hash, display_name, created_at) VALUES (?, ?, ?, ?)",
            ("admin", _hash_pw("admin123"), "System Admin", _now())
        )
    conn.commit()
    conn.close()

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_admin(username: str, password: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT password_hash FROM admin_users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    return row["password_hash"] == _hash_pw(password)

def get_admin_display(username: str) -> str:
    conn = get_conn()
    row = conn.execute(
        "SELECT display_name FROM admin_users WHERE username=?", (username,)
    ).fetchone()
    conn.close()
    return row["display_name"] if row else username

# ─── Config helpers ──────────────────────────────────────────────────────────
def get_config(key: str) -> List[str]:
    try:
        conn = get_conn()
        row = conn.execute("SELECT value_json FROM config_lists WHERE key=?", (key,)).fetchone()
        conn.close()
        if row:
            return json.loads(row["value_json"])
    except Exception:
        pass
    return []

def set_config(key: str, values: List[str]):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO config_lists (key, value_json) VALUES (?, ?)",
        (key, json.dumps(values))
    )
    conn.commit()
    conn.close()

def get_tax_rate(state: str) -> float:
    if not state:
        return 0.0
    conn = get_conn()
    row = conn.execute(
        "SELECT rate FROM tax_rates WHERE state=?", (state.upper().strip(),)
    ).fetchone()
    conn.close()
    return float(row["rate"]) if row else 0.0

def set_tax_rate(state: str, rate: float):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO tax_rates (state, rate) VALUES (?, ?)",
        (state.upper().strip(), rate)
    )
    conn.commit()
    conn.close()

# ─── Archive helpers ─────────────────────────────────────────────────────────
def archive_service(name: str, service_type: str):
    name = name.strip()
    if not name:
        return
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO service_archive (name, service_type, created_at) VALUES (?, ?, ?)",
        (name, service_type, _now())
    )
    conn.commit()
    conn.close()

def get_archived_services(service_type: Optional[str] = None) -> List[str]:
    conn = get_conn()
    if service_type:
        rows = conn.execute(
            "SELECT name FROM service_archive WHERE service_type=? ORDER BY name",
            (service_type,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT name FROM service_archive ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]

def archive_channel(name: str):
    name = name.strip()
    if not name:
        return
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO channel_archive (name, created_at) VALUES (?, ?)",
        (name, _now())
    )
    conn.commit()
    conn.close()

def get_archived_channels() -> List[str]:
    conn = get_conn()
    rows = conn.execute("SELECT name FROM channel_archive ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]

def get_discounts() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, label, disc_type, value FROM discount_archive ORDER BY label"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_discount(label: str, disc_type: str, value: float):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO discount_archive (label, disc_type, value, created_at) VALUES (?, ?, ?, ?)",
        (label.strip(), disc_type, value, _now())
    )
    conn.commit()
    conn.close()

def archive_pattern(pattern: str, label: str = ""):
    pattern = pattern.upper().strip()
    if not pattern or set(pattern) - {"Y", "N"}:
        return
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO pattern_archive (pattern, label, created_at) VALUES (?, ?, ?)",
        (pattern, label or pattern, _now())
    )
    conn.commit()
    conn.close()

def get_patterns() -> List[Dict]:
    conn = get_conn()
    rows = conn.execute("SELECT pattern, label FROM pattern_archive ORDER BY pattern").fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ─── Submission CRUD ─────────────────────────────────────────────────────────
def create_submission(data: Dict[str, Any]) -> int:
    from utils.validation import validate_submission
    result = validate_submission(data)
    if not result.ok:
        raise ValueError("Validation failed: " + "; ".join(result.errors))
    conn = get_conn()
    now = _now()
    cur = conn.execute(
        """
        INSERT INTO submissions (
            created_at, updated_at, status,
            cust_first, cust_last, cust_phone, cust_mobile, cust_email,
            cust_street, cust_city, cust_state, cust_zip,
            property_sqft, areas_serviced, grass_type, special_params,
            services_json,
            emp_id, rep_first, rep_last, rep_email, business_unit, region, sales_channel,
            payment_type, prepay_pct,
            subtotal, total_discount, total_tax, grand_total,
            exception_reason, sales_notes
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            now, now, "pending",
            data.get("cust_first"), data.get("cust_last"), data.get("cust_phone"),
            data.get("cust_mobile"), data.get("cust_email"),
            data.get("cust_street"), data.get("cust_city"), data.get("cust_state"),
            data.get("cust_zip"),
            data.get("property_sqft"), json.dumps(data.get("areas_serviced", [])),
            data.get("grass_type"), json.dumps(data.get("special_params", [])),
            json.dumps(data.get("services", [])),
            data.get("emp_id"), data.get("rep_first"), data.get("rep_last"),
            data.get("rep_email"), data.get("business_unit"), data.get("region"),
            data.get("sales_channel"),
            data.get("payment_type"), data.get("prepay_pct", 0),
            data.get("subtotal", 0), data.get("total_discount", 0),
            data.get("total_tax", 0), data.get("grand_total", 0),
            data.get("exception_reason"), data.get("sales_notes"),
        )
    )
    sid = cur.lastrowid
    conn.execute(
        "INSERT INTO audit_log (submission_id, action, actor, details, created_at) VALUES (?,?,?,?,?)",
        (sid, "created", data.get("emp_id", "unknown"), "Sale submitted", now)
    )
    conn.commit()
    conn.close()
    # Normalize employee → region / branch mapping
    try:
        upsert_employee(
            data.get("emp_id", ""),
            data.get("rep_first", ""),
            data.get("rep_last", ""),
            data.get("rep_email", ""),
            data.get("business_unit", ""),
            data.get("region", ""),
            data.get("branch", "") or data.get("business_unit", ""),
        )
    except Exception:
        pass
    return sid

def update_submission_status(
    sid: int,
    new_status: str,
    actor: str,
    admin_notes: str = "",
    kick_reason: str = ""
) -> bool:
    try:
        actor = normalize_processor_name(actor) or (actor or "").strip()
    except Exception:
        actor = (actor or "").strip()
    conn = get_conn()
    now = _now()
    row = conn.execute(
        "SELECT emp_id, status, rep_email, cust_first, cust_last FROM submissions WHERE id=?",
        (sid,)
    ).fetchone()
    if not row:
        conn.close()
        return False

    old_status = row["status"]
    conn.execute(
        """
        UPDATE submissions SET
            status = ?, updated_at = ?, admin_user = ?, admin_notes = ?,
            kick_reason = ?, processed_at = ?, notified = 0
        WHERE id = ?
        """,
        (new_status, now, actor, admin_notes, kick_reason,
         now if new_status in ("completed", "kicked") else None, sid)
    )
    # In-app notification
    msg = f"Your sale submission #{sid} status changed from '{old_status}' to '{new_status}'."
    if kick_reason:
        msg += f" Kick reason: {kick_reason}"
    if admin_notes:
        msg += f" Notes: {admin_notes}"
    conn.execute(
        "INSERT INTO notifications (emp_id, submission_id, message, created_at) VALUES (?,?,?,?)",
        (row["emp_id"], sid, msg, now)
    )
    conn.execute(
        "INSERT INTO audit_log (submission_id, action, actor, details, created_at) VALUES (?,?,?,?,?)",
        (sid, f"status->{new_status}", actor, admin_notes or kick_reason or "", now)
    )
    conn.commit()
    conn.close()

    # Email notification (best-effort, never blocks workflow)
    try:
        from utils.email_notify import send_status_email
        to_email = row["rep_email"] or ""
        cust = f"{row['cust_first'] or ''} {row['cust_last'] or ''}".strip()
        send_status_email(
            to_email=to_email,
            submission_id=sid,
            old_status=old_status,
            new_status=new_status,
            customer_name=cust,
            admin_notes=admin_notes,
            kick_reason=kick_reason,
        )
    except Exception:
        pass

    return True

def get_submissions(
    status: Optional[str] = None,
    emp_id: Optional[str] = None,
    limit: int = 500
) -> List[Dict]:
    conn = get_conn()
    q = "SELECT * FROM submissions WHERE 1=1"
    params: List[Any] = []
    if status:
        q += " AND status=?"
        params.append(status)
    if emp_id:
        q += " AND emp_id=?"
        params.append(emp_id)
    q += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_submission(sid: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM submissions WHERE id=?", (sid,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_notifications(emp_id: str, unread_only: bool = False) -> List[Dict]:
    conn = get_conn()
    q = "SELECT * FROM notifications WHERE emp_id=?"
    params: List[Any] = [emp_id]
    if unread_only:
        q += " AND read_flag=0"
    q += " ORDER BY created_at DESC LIMIT 50"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_notifications_read(emp_id: str):
    conn = get_conn()
    conn.execute("UPDATE notifications SET read_flag=1 WHERE emp_id=?", (emp_id,))
    conn.commit()
    conn.close()


def upsert_employee(emp_id: str, rep_first: str = "", rep_last: str = "",
                    rep_email: str = "", business_unit: str = "",
                    region: str = "", branch: str = ""):
    """Normalize / archive employee → branch / region mapping."""
    emp_id = (emp_id or "").strip()
    if not emp_id:
        return
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO employee_roster (emp_id, rep_first, rep_last, rep_email,
            business_unit, region, branch, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(emp_id) DO UPDATE SET
            rep_first=COALESCE(NULLIF(excluded.rep_first,''), employee_roster.rep_first),
            rep_last=COALESCE(NULLIF(excluded.rep_last,''), employee_roster.rep_last),
            rep_email=COALESCE(NULLIF(excluded.rep_email,''), employee_roster.rep_email),
            business_unit=COALESCE(NULLIF(excluded.business_unit,''), employee_roster.business_unit),
            region=COALESCE(NULLIF(excluded.region,''), employee_roster.region),
            branch=COALESCE(NULLIF(excluded.branch,''), employee_roster.branch),
            updated_at=excluded.updated_at
        """,
        (emp_id, (rep_first or "").strip(), (rep_last or "").strip(),
         (rep_email or "").strip(), (business_unit or "").strip(),
         (region or "").strip(), (branch or "").strip(), _now())
    )
    conn.commit()
    conn.close()

def get_employee(emp_id: str) -> Optional[Dict]:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM employee_roster WHERE emp_id=?", ((emp_id or "").strip(),)
        ).fetchone()
    except Exception:
        row = None
    conn.close()
    return dict(row) if row else None

def list_employees() -> List[Dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM employee_roster ORDER BY rep_last, rep_first"
        ).fetchall()
    except Exception:
        rows = []
    conn.close()
    return [dict(r) for r in rows]

def get_all_notes_text() -> Dict[str, str]:
    """Concatenate sales notes and kick notes for word-cloud analysis."""
    conn = get_conn()
    sales = conn.execute(
        "SELECT sales_notes FROM submissions WHERE sales_notes IS NOT NULL AND sales_notes != ''"
    ).fetchall()
    kicks = conn.execute(
        "SELECT kick_reason, admin_notes FROM submissions WHERE status='kicked'"
    ).fetchall()
    conn.close()
    sales_blob = " ".join((r[0] or "") for r in sales)
    kick_blob = " ".join(
        f"{(r[0] or '')} {(r[1] or '')}" for r in kicks
    )
    return {"sales": sales_blob, "kicks": kick_blob}

def get_submissions_filtered(
    status: Optional[str] = None,
    period: str = "all",  # week | month | year | all
    region: Optional[str] = None,
    limit: int = 2000,
) -> List[Dict]:
    conn = get_conn()
    q = "SELECT * FROM submissions WHERE 1=1"
    params: List[Any] = []
    if status and status != "all":
        q += " AND status=?"
        params.append(status)
    if period == "week":
        q += " AND created_at >= datetime('now', '-7 days')"
    elif period == "month":
        q += " AND created_at >= datetime('now', '-30 days')"
    elif period == "year":
        q += " AND created_at >= datetime('now', '-365 days')"
    if region and region != "All":
        q += " AND region=?"
        params.append(region)
    q += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    try:
        rows = conn.execute(q, params).fetchall()
    except Exception:
        rows = []
    conn.close()
    return [dict(r) for r in rows]



def upsert_processor(name: str):
    """Normalize processor display names."""
    name = (name or "").strip()
    if not name or len(name) < 2:
        return
    # Title-case normalization while preserving intentional casing of short tokens
    display = " ".join(part.capitalize() if part.islower() or part.isupper() else part for part in name.split())
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO processor_roster (name, display_name, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                display_name=excluded.display_name,
                updated_at=excluded.updated_at
            """,
            (name.lower(), display, _now())
        )
        conn.commit()
    except Exception:
        pass
    conn.close()
    return display

def list_processors() -> List[str]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT display_name FROM processor_roster ORDER BY display_name"
        ).fetchall()
    except Exception:
        rows = []
    conn.close()
    return [r[0] for r in rows if r[0]]

def normalize_processor_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return ""
    display = upsert_processor(name)
    return display or name

def update_full_submission(sid: int, data: Dict[str, Any], actor: str) -> bool:
    """Edit an existing submission (correct manual entry errors)."""
    conn = get_conn()
    now = _now()
    row = conn.execute("SELECT id, status FROM submissions WHERE id=?", (sid,)).fetchone()
    if not row:
        conn.close()
        return False
    conn.execute(
        """
        UPDATE submissions SET
            updated_at=?,
            cust_first=?, cust_last=?, cust_phone=?, cust_mobile=?, cust_email=?,
            cust_street=?, cust_city=?, cust_state=?, cust_zip=?,
            property_sqft=?, areas_serviced=?, grass_type=?, special_params=?,
            services_json=?,
            emp_id=?, rep_first=?, rep_last=?, rep_email=?,
            business_unit=?, region=?, sales_channel=?,
            payment_type=?, prepay_pct=?,
            subtotal=?, total_discount=?, total_tax=?, grand_total=?,
            exception_reason=?, sales_notes=?,
            status=COALESCE(?, status)
        WHERE id=?
        """,
        (
            now,
            data.get("cust_first"), data.get("cust_last"), data.get("cust_phone"),
            data.get("cust_mobile"), data.get("cust_email"),
            data.get("cust_street"), data.get("cust_city"), data.get("cust_state"),
            data.get("cust_zip"),
            data.get("property_sqft"), json.dumps(data.get("areas_serviced", [])),
            data.get("grass_type"), json.dumps(data.get("special_params", [])),
            json.dumps(data.get("services", [])),
            data.get("emp_id"), data.get("rep_first"), data.get("rep_last"),
            data.get("rep_email"),
            data.get("business_unit"), data.get("region"), data.get("sales_channel"),
            data.get("payment_type"), data.get("prepay_pct", 0),
            data.get("subtotal", 0), data.get("total_discount", 0),
            data.get("total_tax", 0), data.get("grand_total", 0),
            data.get("exception_reason"), data.get("sales_notes"),
            data.get("status"),
            sid,
        )
    )
    conn.execute(
        "INSERT INTO audit_log (submission_id, action, actor, details, created_at) VALUES (?,?,?,?,?)",
        (sid, "edited", actor, "Full record corrected", now)
    )
    conn.commit()
    conn.close()
    return True

def delete_submission(sid: int, actor: str) -> bool:
    """Permanently delete a submission (with audit trail entry first)."""
    conn = get_conn()
    now = _now()
    row = conn.execute("SELECT id FROM submissions WHERE id=?", (sid,)).fetchone()
    if not row:
        conn.close()
        return False
    conn.execute(
        "INSERT INTO audit_log (submission_id, action, actor, details, created_at) VALUES (?,?,?,?,?)",
        (sid, "deleted", actor, f"Submission #{sid} permanently deleted", now)
    )
    conn.execute("DELETE FROM notifications WHERE submission_id=?", (sid,))
    conn.execute("DELETE FROM submissions WHERE id=?", (sid,))
    conn.commit()
    conn.close()
    return True


def get_analytics_data() -> Dict[str, Any]:
    conn = get_conn()
    # Status counts
    status_counts = {
        r["status"]: r["cnt"]
        for r in conn.execute(
            "SELECT status, COUNT(*) as cnt FROM submissions GROUP BY status"
        ).fetchall()
    }
    # Top submitters
    top_reps = [
        dict(r) for r in conn.execute(
            """
            SELECT emp_id, rep_first || ' ' || rep_last as name, COUNT(*) as cnt
            FROM submissions GROUP BY emp_id ORDER BY cnt DESC LIMIT 15
            """
        ).fetchall()
    ]
    # Top processors
    top_admins = [
        dict(r) for r in conn.execute(
            """
            SELECT admin_user, COUNT(*) as cnt
            FROM submissions WHERE admin_user IS NOT NULL
            GROUP BY admin_user ORDER BY cnt DESC LIMIT 10
            """
        ).fetchall()
    ]
    # Exception reasons
    reasons = [
        dict(r) for r in conn.execute(
            """
            SELECT exception_reason as reason, COUNT(*) as cnt
            FROM submissions WHERE exception_reason IS NOT NULL AND exception_reason != ''
            GROUP BY exception_reason ORDER BY cnt DESC
            """
        ).fetchall()
    ]
    # Kick reasons
    kicks = [
        dict(r) for r in conn.execute(
            """
            SELECT kick_reason as reason, COUNT(*) as cnt
            FROM submissions WHERE status='kicked' AND kick_reason IS NOT NULL
            GROUP BY kick_reason ORDER BY cnt DESC
            """
        ).fetchall()
    ]
    # Volume by day (last 60)
    daily = [
        dict(r) for r in conn.execute(
            """
            SELECT date(created_at) as day, COUNT(*) as cnt
            FROM submissions
            WHERE created_at >= date('now', '-60 days')
            GROUP BY day ORDER BY day
            """
        ).fetchall()
    ]
    # Totals
    totals = conn.execute(
        """
        SELECT
            COUNT(*) as total_subs,
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status='kicked' THEN 1 ELSE 0 END) as kicked,
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status='audit' THEN 1 ELSE 0 END) as audit,
            COALESCE(SUM(grand_total),0) as revenue,
            COALESCE(AVG(grand_total),0) as avg_ticket
        FROM submissions
        """
    ).fetchone()
    conn.close()
    return {
        "status_counts": status_counts,
        "top_reps": top_reps,
        "top_admins": top_admins,
        "reasons": reasons,
        "kicks": kicks,
        "daily": daily,
        "totals": dict(totals) if totals else {},
    }

def log_audit(sid: int, action: str, actor: str, details: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO audit_log (submission_id, action, actor, details, created_at) VALUES (?,?,?,?,?)",
        (sid, action, actor, details, _now())
    )
    conn.commit()
    conn.close()

# Call init_db() explicitly from app entry points (Home.py / pages)
