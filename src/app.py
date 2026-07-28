"""
app.py

Author: Diego Lopez
Project: Embedded Security Monioring System

Description:
Act as the main entry point for the Embedded Security
Monitoring System.
"""

from motion import start_monitoring
from logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    start_monitoring()