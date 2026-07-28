"""
logging_config.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Provides centralized logging configuration for the monitoring system.
"""

import logging

LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s | %(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """
    Configure application-wide logging.

    Logs are currently written to the terminal. When the application
    is later run through systemd, these messages will be captured by
    the system journal.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT
    )