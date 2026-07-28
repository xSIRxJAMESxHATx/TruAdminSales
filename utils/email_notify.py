"""
Email notification helper for status changes.
Uses SMTP settings stored in config_lists (key: email_settings).
Fails silently if not configured – never blocks the workflow.
"""
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from utils.db import get_config, get_conn


def get_email_settings() -> dict:
    """Return SMTP settings dict or empty defaults."""
    raw = get_config("email_settings")
    # get_config returns list; we store a single JSON string as one-element list
    if isinstance(raw, list) and raw:
        try:
            return json.loads(raw[0]) if isinstance(raw[0], str) else raw[0]
        except Exception:
            pass
    return {
        "enabled": False,
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_pass": "",
        "from_email": "",
        "use_tls": True,
    }


def save_email_settings(settings: dict):
    """Persist settings as a one-item JSON list under config_lists."""
    from utils.db import set_config
    set_config("email_settings", [json.dumps(settings)])


def send_status_email(
    to_email: str,
    submission_id: int,
    old_status: str,
    new_status: str,
    customer_name: str,
    admin_notes: str = "",
    kick_reason: str = "",
) -> tuple[bool, str]:
    """
    Attempt to send a status-change email.
    Returns (success, message).
    """
    if not to_email or "@" not in to_email:
        return False, "No valid recipient email"

    settings = get_email_settings()
    if not settings.get("enabled"):
        return False, "Email notifications disabled"

    host = settings.get("smtp_host", "").strip()
    user = settings.get("smtp_user", "").strip()
    password = settings.get("smtp_pass", "")
    from_addr = settings.get("from_email", "").strip() or user
    port = int(settings.get("smtp_port") or 587)
    use_tls = bool(settings.get("use_tls", True))

    if not host or not from_addr:
        return False, "SMTP not fully configured"

    subject = f"Exception Sale #{submission_id} → {new_status.upper()}"
    body_lines = [
        f"Your system-exception sale submission has been updated.",
        "",
        f"  Submission ID : #{submission_id}",
        f"  Customer      : {customer_name}",
        f"  Previous      : {old_status}",
        f"  New status    : {new_status}",
    ]
    if kick_reason:
        body_lines.append(f"  Kick reason   : {kick_reason}")
    if admin_notes:
        body_lines.append(f"  Admin notes   : {admin_notes}")
    body_lines += [
        "",
        "Log in to the Exception Sales portal → My Submissions to view full details.",
        "",
        "— Lawn Care Exception Sales System",
    ]
    body = "\n".join(body_lines)

    msg = MIMEMultipart()
    msg["From"] = from_addr
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        if use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=20) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                if user and password:
                    server.login(user, password)
                server.sendmail(from_addr, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=20) as server:
                if user and password:
                    server.login(user, password)
                server.sendmail(from_addr, [to_email], msg.as_string())
        return True, "Email sent"
    except Exception as e:
        return False, str(e)
