"""
motion.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Monitors the PIR motion sensor and coordinates the system response when
motion is detected. This module integrates the motion sensor, camera,
and database subsystems into a single, event-driven workflow.
"""

import logging

from gpiozero import MotionSensor
from signal import pause

#MEDIA_DIR is imported so relative file paths can be stored
#instead of machine-specific absolute paths.
from camera import take_photo, record_video, MEDIA_DIR
from database import initialize_database, add_event
from storage_manager import cleanup_if_needed
from logging_config import setup_logging
from notification import send_motion_notification

logger = logging.getLogger(__name__)

#Duration of each motion-triggered recording
VIDEO_DURATION_SECONDS = 10
VIDEO_DURATION_MS = VIDEO_DURATION_SECONDS * 1000


def handle_motion_event():
    """
    Handles everything that should happen after motion is detected.

    Current Responsibilities:
    -Check available storage
    -Take a photo
    -Record a video
    -Log the event to the database
    -Send a push notification
    """

    try:
        #Check available storage before creating new media.
        logger.info("Checking available storage.")
        cleanup_if_needed()

        logger.info("Capturing photo...")
        photo_path, timestamp = take_photo()
        logger.info(
            "Photo saved successfully: %s",
            photo_path
        )
    
        logger.info("Recording video...")
        video_path, _ = record_video(duration_ms=VIDEO_DURATION_MS)
        logger.info(
            "Video saved successfully: %s",
            video_path
        )
    
        logger.info("Saving motion event to database...")
        #Store the completed motion event in the SQLite database.
        event_id = add_event(
            timestamp=timestamp,
            photo_path=str(photo_path.relative_to(MEDIA_DIR.parent)),
            video_path=str(video_path.relative_to(MEDIA_DIR.parent)),
            duration_seconds=VIDEO_DURATION_SECONDS
        )

        logger.info(
            "Motion event #%s completed and stored successfully.",
            event_id
        )

        #Send a push notification after the event has been fully recorded.
        send_motion_notification(
            event_id=event_id,
            timestamp=timestamp
        )
    
    except Exception:
        logger.exception("Motion event failed. Monitoring will continue.")

def motion_detected():
    """
    Callback function that runs when the PIR sensor detects motion.
    """

    logger.info("Motion detected.")
    handle_motion_event()
    logger.info("Waiting for the next motion event...")

def start_monitoring():
    """
    Initialize the motion monitoring system and begin
    listening for motion events.
    """

    # PIR sensor output is connected to GPIO17, physical pin 11.
    pir = MotionSensor(17)

    #Ensure database exists before monitoring begins
    initialize_database()

    logger.info("Embedded Security Monitoring System Starting.")
    logger.info("Motion sensor initialized on GPIO17.")
    logger.info("Waiting for motion...")

    #Register callback function
    pir.when_motion = motion_detected

    #Keep the program running indefinitely
    pause()

#Only start monitoring if this file is executed directly. This
#allows app.py to import start_monitoring() without immediately
#starting the sensor.
if __name__ == "__main__":
    setup_logging()
    start_monitoring()
