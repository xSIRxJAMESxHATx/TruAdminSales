"""
Pricing, discount, and tax calculation helpers.
"""
from typing import List, Dict, Any, Tuple
from utils.db import get_tax_rate


def calc_service_line(
    price_per_app: float,
    num_apps: int,
    discounts: List[Dict[str, Any]],
    tax_rate: float,
    is_last_app_free: bool = False,
) -> Dict[str, float]:
    """
    discounts: list of {"type": "percent"|"dollar", "value": float, "label": str}
    Returns subtotal, discount_amount, taxable, tax, total for one service line.
    """
    if num_apps < 1:
        num_apps = 1
    base = float(price_per_app) * num_apps

    # Handle "Last app free" specially
    if is_last_app_free and num_apps > 0:
        base = float(price_per_app) * (num_apps - 1)

    disc_amt = 0.0
    for d in discounts:
        if d.get("type") == "percent":
            disc_amt += base * (float(d.get("value", 0)) / 100.0)
        else:
            disc_amt += float(d.get("value", 0))

    # Cap discount at base
    disc_amt = min(disc_amt, base)
    after_disc = max(0.0, base - disc_amt)
    tax = after_disc * tax_rate
    total = after_disc + tax

    return {
        "base": round(base, 2),
        "discount": round(disc_amt, 2),
        "after_discount": round(after_disc, 2),
        "tax": round(tax, 2),
        "total": round(total, 2),
    }


def calc_order_totals(
    services: List[Dict[str, Any]],
    state: str,
    prepay_pct: float = 0.0,
) -> Dict[str, float]:
    """
    services: each has already-calculated line totals or raw fields.
    Prefer pre-calculated 'line_total', 'line_discount', 'line_tax' if present.
    """
    tax_rate = get_tax_rate(state)
    subtotal = 0.0
    total_disc = 0.0
    total_tax = 0.0

    for s in services:
        if "line_total" in s:
            subtotal += s.get("line_base", s.get("line_total", 0))
            total_disc += s.get("line_discount", 0)
            total_tax += s.get("line_tax", 0)
        else:
            # fallback recalculation
            discounts = s.get("discounts", [])
            is_laf = any(
                "last app free" in (d.get("label") or "").lower() for d in discounts
            )
            line = calc_service_line(
                s.get("price_per_app", 0),
                s.get("num_apps", 1),
                discounts,
                tax_rate,
                is_last_app_free=is_laf,
            )
            subtotal += line["base"]
            total_disc += line["discount"]
            total_tax += line["tax"]

    after_disc = max(0.0, subtotal - total_disc)
    # Prepay discount applies to after-discount, pre-tax amount
    prepay_disc = 0.0
    if prepay_pct and prepay_pct > 0:
        prepay_disc = after_disc * (prepay_pct / 100.0)
        after_disc -= prepay_disc
        total_disc += prepay_disc
        # Recalculate tax on new after_disc
        total_tax = after_disc * tax_rate

    grand = after_disc + total_tax

    return {
        "subtotal": round(subtotal, 2),
        "total_discount": round(total_disc, 2),
        "total_tax": round(total_tax, 2),
        "grand_total": round(grand, 2),
        "tax_rate": tax_rate,
        "prepay_discount": round(prepay_disc, 2),
    }


def pattern_from_selection(selected: List[int], max_rounds: int = 8) -> str:
    """selected: list of 1-based round numbers that are YES."""
    bits = ["N"] * max_rounds
    for i in selected:
        if 1 <= i <= max_rounds:
            bits[i - 1] = "Y"
    return "".join(bits)
