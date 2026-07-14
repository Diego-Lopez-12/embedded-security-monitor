"""
motion_camera_test.py

Purpose:
Test integration between the PIR motion sensor and the camera module.
When motion is detected, the program captures a photo and records a video.
"""

from gpiozero import MotionSensor
from signal import pause

#MEDIA_DIR is imported so relative file paths can be stored
#instead of macine-specific absolute paths.
from camera import take_photo, record_video, MEDIA_DIR
from database import initialize_database, add_event


# PIR sensor output is connected to GPIO17, physical pin 11.
pir = MotionSensor(17)

#Duration of each motion-triggered recording
VIDEO_DURATION_SECONDS = 10
VIDEO_DURATION_MS = VIDEO_DURATION_SECONDS * 1000


def handle_motion_event():
    """
    Handles everything that should happen after motion is detected.

    Current Responsibilities:
    -Take a photo
    -Record a video
    -Log the event to the database

    Later, add:
    -notifications
    -dashboard updates
    -Storage management
    """

    print("Capturing photo...")
    photo_path, timestamp = take_photo()
    print(f"Photo saved to: {photo_path}")

    print("Recording video...")
    video_path, _ = record_video(duration_ms=VIDEO_DURATION_MS)
    print(f"Video saved to: {video_path}")

    print("Logging event to database...")
    add_event(
        timestamp=timestamp,
        photo_path=str(photo_path.relative_to(MEDIA_DIR.parent)),
        video_path=str(video_path.relative_to(MEDIA_DIR.parent)),
        duration_seconds=VIDEO_DURATION_SECONDS
    )

    print("Motion event logged.")
    print("Motion event complete. Waiting for next motion...")


def motion_detected():
    """
    Callback function that runs when the PIR sensor detects motion.
    """

    print("Motion detected.")
    handle_motion_event()


#Make sure database and events table exists
#before listening for motion events
initialize_database()

("Motion-camera test initialized.")
print("Waiting for motion...")

# Give gpiozero the function reference.
# Do not use parentheses here.
pir.when_motion = motion_detected

# Keep program running.
pause()