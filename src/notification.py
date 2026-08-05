"""
notification.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Sends optional push notifications after successful motion events.
Uses ntfy and includes a cooldown to prevent repeated alerts.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv


logger = logging.getLogger(__name__)

# Determine the project root from src/notification.py.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load private settings from the project-level .env file.
load_dotenv(PROJECT_ROOT / ".env")


def get_boolean_environment_variable(name, default=False):
    """
    Read a true/false value from an environment variable.
    """

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in (
        "true",
        "1",
        "yes",
        "on"
    )


PUSH_NOTIFICATIONS_ENABLED = get_boolean_environment_variable(
    "PUSH_NOTIFICATIONS_ENABLED",
    default=False
)

PUSH_NOTIFICATION_COOLDOWN_SECONDS = int(
    os.getenv(
        "PUSH_NOTIFICATION_COOLDOWN_SECONDS",
        "60"
    )
)

NTFY_SERVER_URL = os.getenv(
    "NTFY_SERVER_URL",
    "https://ntfy.sh"
).rstrip("/")

NTFY_TOPIC = os.getenv("NTFY_TOPIC")

SECURITY_DASHBOARD_URL = os.getenv(
    "SECURITY_DASHBOARD_URL",
    "http://security-pi:5000"
)

# Store when the most recent notification was sent successfully.
_last_notification_time = None


def notification_configuration_is_valid():
    """
    Verify that a private ntfy topic has been configured.
    """

    return bool(NTFY_TOPIC)


def notification_is_in_cooldown():
    """
    Return True if a notification was sent too recently.
    """

    if _last_notification_time is None:
        return False

    elapsed_seconds = (
        time.monotonic() - _last_notification_time
    )

    return (
        elapsed_seconds
        < PUSH_NOTIFICATION_COOLDOWN_SECONDS
    )


def format_notification_timestamp(timestamp):
    """
    Convert the stored timestamp into a readable date and time.

    Example:
        2026-08-04_17-42-10
        becomes
        August 4, 2026 at 5:42 PM
    """

    try:
        parsed_timestamp = datetime.strptime(
            timestamp,
            "%Y-%m-%d_%H-%M-%S"
        )

        month = parsed_timestamp.strftime("%B")
        day = parsed_timestamp.day
        year = parsed_timestamp.year

        time_display = parsed_timestamp.strftime(
            "%I:%M %p"
        ).lstrip("0")

        return (
            f"{month} {day}, {year} at "
            f"{time_display}"
        )

    except (TypeError, ValueError):
        # Preserve the original value if the format is unexpected.
        return timestamp


def build_notification_payload(event_id, timestamp):
    """
    Build the notification data sent to ntfy.
    """

    readable_timestamp = format_notification_timestamp(
        timestamp
    )

    return {
        "topic": NTFY_TOPIC,
        "title": "Motion Detected",
        "message": (
            f"Motion event #{event_id} was recorded "
            f"{readable_timestamp}."
        ),
        "priority": 4,
        "tags": [
            "camera",
            "warning"
        ],

        # Tapping the notification opens the private dashboard.
        "click": SECURITY_DASHBOARD_URL
    }


def send_motion_notification(event_id, timestamp):
    """
    Send a push notification for a completed motion event.

    Notification failures are logged without stopping monitoring.

    Returns:
        True if the notification was submitted successfully.
        False if disabled, skipped, or unsuccessful.
    """

    global _last_notification_time

    if not PUSH_NOTIFICATIONS_ENABLED:
        logger.info(
            "Push notification skipped because notifications "
            "are disabled."
        )
        return False

    if not notification_configuration_is_valid():
        logger.error(
            "Push notification configuration is incomplete."
        )
        return False

    if notification_is_in_cooldown():
        logger.info(
            "Push notification skipped because the cooldown "
            "is still active."
        )
        return False

    payload = build_notification_payload(
        event_id,
        timestamp
    )

    request = Request(
        f"{NTFY_SERVER_URL}/",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        # Keep the timeout short so notification problems do not
        # delay or stop the monitoring application.
        with urlopen(request, timeout=10) as response:
            if not 200 <= response.status < 300:
                logger.error(
                    "ntfy returned unexpected status code: %s",
                    response.status
                )
                return False

        # Start the cooldown only after ntfy accepts the alert.
        _last_notification_time = time.monotonic()

        logger.info(
            "Push notification submitted successfully "
            "for event #%s.",
            event_id
        )

        return True

    except HTTPError as error:
        logger.error(
            "ntfy rejected the notification with HTTP status %s.",
            error.code
        )

    except URLError as error:
        logger.error(
            "Could not reach ntfy: %s",
            error.reason
        )

    except Exception:
        logger.exception(
            "Push notification failed. Monitoring will continue."
        )

    return False