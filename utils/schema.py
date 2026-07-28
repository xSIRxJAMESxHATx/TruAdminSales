"""
Refined JSON schemas for exception sales submissions and nested services.

Used for documentation, Power BI field mapping, and runtime validation.
"""
from __future__ import annotations

from typing import Any, Dict, List

# ─── Service line schema (one object inside services_json array) ─────────────
SERVICE_LINE_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://lawncare.local/schemas/service-line.json",
    "title": "ServiceLine",
    "type": "object",
    "additionalProperties": True,
    "required": ["name", "service_type", "num_apps", "price"],
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 120,
            "description": "Service display name (archived for future dropdowns).",
        },
        "service_type": {
            "type": "string",
            "enum": ["lawn", "expanded", "tree"],
            "description": "Category of service line.",
        },
        "num_apps": {
            "type": "integer",
            "minimum": 1,
            "maximum": 24,
            "description": "Number of applications for the year.",
        },
        "price": {
            "type": "number",
            "minimum": 0.01,
            "maximum": 50000,
            "description": "Price per application in USD.",
        },
        "discounts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["label", "type", "value"],
                "properties": {
                    "label": {"type": "string"},
                    "type": {"type": "string", "enum": ["percent", "dollar"]},
                    "value": {"type": "number", "minimum": 0},
                    "disc_type": {"type": "string", "enum": ["percent", "dollar"]},
                },
            },
            "description": "Applied discount templates and custom amounts.",
        },
        "disc_labels": {
            "type": "array",
            "items": {"type": "string"},
        },
        "pattern": {
            "type": "string",
            "pattern": "^[YN]{0,8}$",
            "description": "Tree & shrub round pattern, e.g. YNNYYNY (max 8 rounds).",
        },
        "rounds": {
            "type": "array",
            "items": {"type": "integer", "minimum": 1, "maximum": 8},
        },
        "line_base": {"type": "number", "minimum": 0},
        "line_discount": {"type": "number", "minimum": 0},
        "line_tax": {"type": "number", "minimum": 0},
        "line_total": {"type": "number", "minimum": 0},
    },
}

# ─── Full submission payload schema ──────────────────────────────────────────
SUBMISSION_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://lawncare.local/schemas/submission.json",
    "title": "ExceptionSaleSubmission",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "cust_first", "cust_last", "cust_phone",
        "cust_street", "cust_city", "cust_state", "cust_zip",
        "emp_id", "rep_first", "rep_last",
        "business_unit", "region",
        "payment_type", "exception_reason",
        "services",
    ],
    "properties": {
        "cust_first": {"type": "string", "minLength": 1, "maxLength": 80},
        "cust_last": {"type": "string", "minLength": 1, "maxLength": 80},
        "cust_phone": {
            "type": "string",
            "minLength": 7,
            "maxLength": 20,
            "description": "Primary phone; digits and common separators allowed.",
        },
        "cust_mobile": {"type": "string", "maxLength": 20},
        "cust_email": {
            "type": "string",
            "maxLength": 120,
            "description": "Optional; validated when non-empty.",
        },
        "cust_street": {"type": "string", "minLength": 1, "maxLength": 120},
        "cust_city": {"type": "string", "minLength": 1, "maxLength": 80},
        "cust_state": {
            "type": "string",
            "minLength": 2,
            "maxLength": 2,
            "pattern": "^[A-Za-z]{2}$",
            "description": "US state / DC two-letter code.",
        },
        "cust_zip": {
            "type": "string",
            "pattern": "^[0-9]{5}(-[0-9]{4})?$",
            "description": "ZIP or ZIP+4.",
        },
        "property_sqft": {"type": "number", "minimum": 0, "maximum": 5000000},
        "areas_serviced": {
            "type": "array",
            "items": {"type": "string", "enum": ["Front", "Back", "Right", "Left"]},
        },
        "grass_type": {"type": "string", "maxLength": 60},
        "special_params": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["Locked Gate", "Pet", "Invisible Fence", "Sprinkler System"],
            },
        },
        "services": {
            "type": "array",
            "minItems": 1,
            "items": SERVICE_LINE_SCHEMA,
            "description": "One or more service lines; stored as services_json.",
        },
        "emp_id": {"type": "string", "minLength": 1, "maxLength": 40},
        "rep_first": {"type": "string", "minLength": 1, "maxLength": 80},
        "rep_last": {"type": "string", "minLength": 1, "maxLength": 80},
        "rep_email": {"type": "string", "maxLength": 120},
        "business_unit": {"type": "string", "minLength": 1, "maxLength": 80},
        "branch": {"type": "string", "maxLength": 80},
        "region": {"type": "string", "minLength": 1, "maxLength": 80},
        "sales_channel": {"type": "string", "maxLength": 80},
        "payment_type": {
            "type": "string",
            "enum": ["prepay", "easpay", "invoice"],
        },
        "prepay_pct": {"type": "number", "enum": [0, 5, 7, 10]},
        "subtotal": {"type": "number", "minimum": 0},
        "total_discount": {"type": "number", "minimum": 0},
        "total_tax": {"type": "number", "minimum": 0},
        "grand_total": {"type": "number", "minimum": 0},
        "exception_reason": {"type": "string", "minLength": 1, "maxLength": 200},
        "sales_notes": {"type": "string", "maxLength": 4000},
    },
}

# Status lifecycle for documentation / Power BI measures
STATUS_ENUM = ["pending", "processing", "audit", "completed", "kicked"]

# Power BI–oriented field catalog (flat fact table + notes on nested JSON)
POWERBI_FIELD_CATALOG: List[Dict[str, str]] = [
    {"table": "fact_submissions", "column": "id", "type": "Int64", "description": "Surrogate key"},
    {"table": "fact_submissions", "column": "created_at", "type": "DateTime", "description": "UTC submit time"},
    {"table": "fact_submissions", "column": "updated_at", "type": "DateTime", "description": "Last status change"},
    {"table": "fact_submissions", "column": "status", "type": "Text", "description": "pending|processing|audit|completed|kicked"},
    {"table": "fact_submissions", "column": "cust_first", "type": "Text", "description": "Customer first name"},
    {"table": "fact_submissions", "column": "cust_last", "type": "Text", "description": "Customer last name"},
    {"table": "fact_submissions", "column": "cust_phone", "type": "Text", "description": "Primary phone"},
    {"table": "fact_submissions", "column": "cust_email", "type": "Text", "description": "Customer email"},
    {"table": "fact_submissions", "column": "cust_city", "type": "Text", "description": "City"},
    {"table": "fact_submissions", "column": "cust_state", "type": "Text", "description": "2-letter state"},
    {"table": "fact_submissions", "column": "cust_zip", "type": "Text", "description": "ZIP / ZIP+4"},
    {"table": "fact_submissions", "column": "property_sqft", "type": "Double", "description": "Property square feet"},
    {"table": "fact_submissions", "column": "emp_id", "type": "Text", "description": "Sales rep employee ID"},
    {"table": "fact_submissions", "column": "rep_first", "type": "Text", "description": "Rep first name"},
    {"table": "fact_submissions", "column": "rep_last", "type": "Text", "description": "Rep last name"},
    {"table": "fact_submissions", "column": "business_unit", "type": "Text", "description": "Business unit"},
    {"table": "fact_submissions", "column": "region", "type": "Text", "description": "Region"},
    {"table": "fact_submissions", "column": "sales_channel", "type": "Text", "description": "Sales channel"},
    {"table": "fact_submissions", "column": "payment_type", "type": "Text", "description": "prepay|easpay|invoice"},
    {"table": "fact_submissions", "column": "prepay_pct", "type": "Double", "description": "0, 5, 7, or 10"},
    {"table": "fact_submissions", "column": "subtotal", "type": "Double", "description": "Pre-discount subtotal USD"},
    {"table": "fact_submissions", "column": "total_discount", "type": "Double", "description": "All discounts USD"},
    {"table": "fact_submissions", "column": "total_tax", "type": "Double", "description": "Sales tax USD"},
    {"table": "fact_submissions", "column": "grand_total", "type": "Double", "description": "Customer total USD"},
    {"table": "fact_submissions", "column": "exception_reason", "type": "Text", "description": "Why system exception"},
    {"table": "fact_submissions", "column": "kick_reason", "type": "Text", "description": "Reject reason if kicked"},
    {"table": "fact_submissions", "column": "admin_user", "type": "Text", "description": "Processor display name"},
    {"table": "fact_submissions", "column": "processed_at", "type": "DateTime", "description": "Completion/kick time"},
    {"table": "fact_service_lines", "column": "submission_id", "type": "Int64", "description": "FK → fact_submissions"},
    {"table": "fact_service_lines", "column": "name", "type": "Text", "description": "Service name"},
    {"table": "fact_service_lines", "column": "service_type", "type": "Text", "description": "lawn|expanded|tree"},
    {"table": "fact_service_lines", "column": "num_apps", "type": "Int64", "description": "Applications count"},
    {"table": "fact_service_lines", "column": "price", "type": "Double", "description": "Price per app"},
    {"table": "fact_service_lines", "column": "pattern", "type": "Text", "description": "Y/N tree pattern"},
    {"table": "fact_service_lines", "column": "line_total", "type": "Double", "description": "Line total after tax"},
    {"table": "dim_employee", "column": "emp_id", "type": "Text", "description": "Employee natural key"},
    {"table": "dim_employee", "column": "region", "type": "Text", "description": "Normalized region"},
    {"table": "dim_employee", "column": "branch", "type": "Text", "description": "Normalized branch"},
]


def schema_as_json_text() -> str:
    import json
    return json.dumps(
        {
            "submission": SUBMISSION_SCHEMA,
            "service_line": SERVICE_LINE_SCHEMA,
            "status_enum": STATUS_ENUM,
        },
        indent=2,
    )
