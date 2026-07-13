"""
motion_camera_test.py

Purpose:
Test integration between the PIR motion sensor and the camera module.
When motion is detected the program captures a photo and 10-second
video using camera.py
"""

from gpiozero import MotionSensor
from signal import pause

from camera import take_photo, record_video   #Import take_photo() & record_video function from camera.py

#PIR sensor output is connected to GPIO17, physical pin 11
pir = MotionSensor(17)

def motion_detected():
    """
    Runs whenever the PIR sensor detects motion.
    Captures a photo and records a short video
    """
    print("Motion detected.")

    print("Capturing photo...")
    photo_path = take_photo()
    print(f"Photo saved to: {photo_path}")

    print("Recording video...")
    video_path = record_video(duration_ms=10000)
    print(f"Video saved to: {video_path}")

    print("Motion event complete. Waiting for next motion...")

print("Motion-camera test initialized.")
print("Waiting for motion...")

#When motion is detected, call function
pir.when_motion = motion_detected

#Keep Program Running
pause()