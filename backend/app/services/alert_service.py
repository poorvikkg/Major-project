"""
services/alert_service.py
Placeholder for alert/notification logic (email, SMS, push).
Can be expanded to integrate with Twilio, SendGrid, etc.
"""
from __future__ import annotations
from datetime import datetime


def send_detection_alert(
    person_name: str,
    confidence: float,
    location: str | None = None,
    timestamp: datetime | None = None,
) -> dict:
    """
    Send an alert when a missing person is detected.
    Currently logs to console — wire up email/SMS here in production.
    """
    msg = (
        f"🚨 ALERT: Missing person '{person_name}' detected "
        f"with {confidence}% confidence"
    )
    if location:
        msg += f" at {location}"
    if timestamp:
        msg += f" on {timestamp.isoformat()}"

    print(msg)

    return {
        "alert_sent": True,
        "message": msg,
    }
