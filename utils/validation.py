"""
Data validation rules for exception sales intake.

Combines field-level rules, cross-field checks, and optional JSON Schema
validation of the nested services array.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from utils.schema import SUBMISSION_SCHEMA, SERVICE_LINE_SCHEMA, STATUS_ENUM

# US states + DC
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT",
    "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI",
    "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
}

PHONE_RE = re.compile(r"^[\d\s\-\.\(\)\+]{7,20}$")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")
EMP_ID_RE = re.compile(r"^[A-Za-z0-9\-_]{1,40}$")
PATTERN_RE = re.compile(r"^[YN]{0,8}$")


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def error(self, msg: str):
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def extend(self, other: "ValidationResult"):
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


def _digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def validate_phone(label: str, value: str, required: bool = False) -> ValidationResult:
    r = ValidationResult()
    v = (value or "").strip()
    if not v:
        if required:
            r.error(f"{label} is required")
        return r
    if not PHONE_RE.match(v):
        r.error(f"{label} has invalid characters (use digits and common separators)")
    d = _digits(v)
    if len(d) < 10:
        r.error(f"{label} must include at least 10 digits")
    elif len(d) > 15:
        r.error(f"{label} has too many digits")
    return r


def validate_email(label: str, value: str, required: bool = False) -> ValidationResult:
    r = ValidationResult()
    v = (value or "").strip()
    if not v:
        if required:
            r.error(f"{label} is required")
        return r
    if not EMAIL_RE.match(v):
        r.error(f"{label} is not a valid email address")
    if len(v) > 120:
        r.error(f"{label} is too long")
    return r


def validate_state(value: str) -> ValidationResult:
    r = ValidationResult()
    v = (value or "").strip().upper()
    if not v:
        r.error("State is required (2-letter code)")
    elif len(v) != 2:
        r.error("State must be a 2-letter code")
    elif v not in US_STATES:
        r.error(f"State '{v}' is not a recognized US state/DC code")
    return r


def validate_zip(value: str) -> ValidationResult:
    r = ValidationResult()
    v = (value or "").strip()
    if not v:
        r.error("ZIP code is required")
    elif not ZIP_RE.match(v):
        r.error("ZIP must be 5 digits or ZIP+4 (e.g. 78701 or 78701-1234)")
    return r


def validate_service_line(svc: Dict[str, Any], index: int) -> ValidationResult:
    r = ValidationResult()
    label = f"Service #{index + 1}"
    name = (svc.get("name") or "").strip()
    if not name:
        r.error(f"{label}: name is required")
    elif len(name) > 120:
        r.error(f"{label}: name is too long")

    stype = svc.get("service_type") or "lawn"
    if stype not in ("lawn", "expanded", "tree"):
        r.error(f"{label}: invalid service_type '{stype}'")

    try:
        apps = int(svc.get("num_apps") or 0)
    except (TypeError, ValueError):
        apps = 0
    if apps < 1 or apps > 24:
        r.error(f"{label}: # applications must be between 1 and 24")

    try:
        price = float(svc.get("price") or 0)
    except (TypeError, ValueError):
        price = 0.0
    if price <= 0:
        r.error(f"{label}: price per app must be greater than 0")
    elif price > 50000:
        r.error(f"{label}: price per app exceeds maximum ($50,000)")

    pattern = svc.get("pattern") or ""
    if pattern and not PATTERN_RE.match(str(pattern).upper()):
        r.error(f"{label}: pattern must be Y/N only, max 8 characters")

    if stype == "tree" and apps > 8:
        r.warn(f"{label}: tree/shrub pattern supports rounds 1–8; apps={apps}")

    for d in svc.get("discounts") or []:
        try:
            val = float(d.get("value") or 0)
        except (TypeError, ValueError):
            r.error(f"{label}: discount value must be numeric")
            continue
        dtype = d.get("type") or d.get("disc_type") or "percent"
        if dtype == "percent" and (val < 0 or val > 100):
            r.error(f"{label}: percent discount must be 0–100")
        if dtype == "dollar" and val < 0:
            r.error(f"{label}: dollar discount cannot be negative")

    return r


def validate_submission(data: Dict[str, Any]) -> ValidationResult:
    """Full payload validation (form + API / create_submission)."""
    r = ValidationResult()

    # Customer
    if not (data.get("cust_first") or "").strip():
        r.error("Customer first name is required")
    if not (data.get("cust_last") or "").strip():
        r.error("Customer last name is required")
    r.extend(validate_phone("Phone number", data.get("cust_phone") or "", required=True))
    if data.get("cust_mobile"):
        r.extend(validate_phone("Mobile / alt number", data.get("cust_mobile") or ""))
    r.extend(validate_email("Customer email", data.get("cust_email") or "", required=False))
    if not (data.get("cust_street") or "").strip():
        r.error("Street address is required")
    if not (data.get("cust_city") or "").strip():
        r.error("City is required")
    r.extend(validate_state(data.get("cust_state") or ""))
    r.extend(validate_zip(data.get("cust_zip") or ""))

    sqft = data.get("property_sqft")
    if sqft is not None:
        try:
            sf = float(sqft)
            if sf < 0:
                r.error("Property sq ft cannot be negative")
            if sf > 5_000_000:
                r.error("Property sq ft is unrealistically large")
            if 0 < sf < 100:
                r.warn("Property sq ft is very small — confirm value")
        except (TypeError, ValueError):
            r.error("Property sq ft must be a number")

    # Services
    services = data.get("services") or []
    if not services:
        r.error("At least one named service is required")
    else:
        for i, svc in enumerate(services):
            r.extend(validate_service_line(svc, i))

    # Rep
    emp = (data.get("emp_id") or "").strip()
    if not emp:
        r.error("Employee ID is required")
    elif not EMP_ID_RE.match(emp):
        r.error("Employee ID contains invalid characters")
    if not (data.get("rep_first") or "").strip():
        r.error("Rep first name is required")
    if not (data.get("rep_last") or "").strip():
        r.error("Rep last name is required")
    r.extend(validate_email("Rep email", data.get("rep_email") or "", required=False))
    if not (data.get("business_unit") or "").strip():
        r.error("Business unit is required")
    if not (data.get("region") or "").strip():
        r.error("Region is required")

    pay = data.get("payment_type") or ""
    if pay not in ("prepay", "easpay", "invoice"):
        r.error("Payment type must be prepay, easpay, or invoice")
    prepay = data.get("prepay_pct") or 0
    try:
        prepay_f = float(prepay)
    except (TypeError, ValueError):
        prepay_f = -1
    if pay == "prepay" and prepay_f not in (5, 7, 10):
        r.error("Prepay requires a discount of 5%, 7%, or 10%")
    if pay != "prepay" and prepay_f not in (0, 0.0):
        r.warn("Prepay % is set but payment type is not prepay")

    if not (data.get("exception_reason") or "").strip():
        r.error("Exception reason is required")

    notes = data.get("sales_notes") or ""
    if len(notes) > 4000:
        r.error("Sales notes exceed 4,000 characters")
    # Soft check for sensitive data patterns
    sensitive = re.search(
        r"\b(?:\d[ -]*?){13,19}\b|ssn|social security|routing\s*#|account\s*#",
        notes,
        re.I,
    )
    if sensitive:
        r.warn(
            "Sales notes may contain sensitive payment or SSN-like data — "
            "remove before submitting"
        )

    # Totals sanity
    for key in ("subtotal", "total_discount", "total_tax", "grand_total"):
        try:
            val = float(data.get(key) or 0)
            if val < 0:
                r.error(f"{key} cannot be negative")
        except (TypeError, ValueError):
            r.error(f"{key} must be numeric")

    grand = float(data.get("grand_total") or 0)
    if services and grand <= 0:
        r.error("Grand total must be greater than 0")

    # Optional JSON Schema (structural) if jsonschema is installed
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=SUBMISSION_SCHEMA)
    except ImportError:
        pass
    except Exception as e:
        # Schema is strict; surface as warning so field rules remain source of truth
        r.warn(f"JSON schema note: {e}")

    return r


def validate_status_transition(old: str, new: str) -> ValidationResult:
    r = ValidationResult()
    if new not in STATUS_ENUM:
        r.error(f"Invalid status '{new}'")
        return r
    allowed = {
        "pending": {"processing", "audit", "completed", "kicked"},
        "processing": {"audit", "completed", "kicked", "pending"},
        "audit": {"completed", "kicked", "processing"},
        "completed": set(),
        "kicked": set(),
    }
    if old in ("completed", "kicked") and new != old:
        r.warn(f"Re-opening a {old} sale is unusual")
    if old in allowed and new not in allowed[old] and new != old:
        r.warn(f"Unusual transition {old} → {new}")
    return r


def validate_processor_name(name: str) -> ValidationResult:
    r = ValidationResult()
    n = (name or "").strip()
    if not n:
        r.error("Processor name is required")
    elif len(n) < 2:
        r.error("Processor name is too short")
    elif len(n) > 80:
        r.error("Processor name is too long")
    elif not re.search(r"[A-Za-z]", n):
        r.error("Processor name must include letters")
    return r
