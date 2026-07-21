"""
camera.py

Author: Diego Lopez
Project: Embedded Security Monitoring System
Created: June 2026
Version: 1.0

Description:
Provides an interface between the application software and the 
Raspberry Pi Camera Module 3. Handles image capture, video recording,
and media file management so that other project components can
interact with the camera through simple function calls.

Dependencies:
-subprocess
-pathlib
-Raspberry Pi Camera Software (rpicam-still, rpicam-vid)

Functions:
-take_photo()
-record_video()
-generate_timestamp()
"""

import subprocess               #Used to run external programs, execute system commands, and manage new processes directly from code
from pathlib import Path        #For interacting with filesystem paths
from datetime import datetime   #Lets us add timestamps to filenames

#__file__ path to the file: src/camera.py
#parent = src/
#parent.parent = project root folder: embedded-security-monitor/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#Store all camera output in organized project folders
MEDIA_DIR = PROJECT_ROOT / "media"
PHOTO_DIR = MEDIA_DIR / "photos"
VIDEO_DIR = MEDIA_DIR / "videos"

#The Camera Currently Records at 30 Frames per Second
VIDEO_FRAME_RATE = 30

def take_photo(filename: str = None):
    """
    Capture an image using the Raspberry Pi Camera

    Args:
        -filename: Name of the photo file to create
    
    Returns:
        -Full path to the saved photo
        -Timestamp used for filename
    """  
    timestamp = generate_timestamp()

    #Use a timestamp to label the jpg
    if filename is None:
        filename = f"photo_{timestamp}.jpg"

    #Make sure the output folder exists before saving
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PHOTO_DIR / filename

    #Run the Linux Command Used to Take a Photo
    #rpicam-still -o <output_path>
    subprocess.run(["rpicam-still", "-o", str(output_path)], check=True)

    return output_path, timestamp

def record_video(filename: str = None, duration_ms: int = 5000):
    """
    Record a video and store it as a valid MP4 file.

    The Raspberry Pi first records a temporary raw H.264 stream.
    FFmpeg then places that stream inside an MP4 container that
    browsers and desktop media players can understand.

    Args:
        filename: Optional name of the final MP4 file.
        duration_ms: Recording duration in milliseconds.

    Returns:
        A tuple containing:
        - Full path to the saved MP4 video.
        - Timestamp used for the filename.
    """

    timestamp = generate_timestamp()

    if filename is None:
        filename = f"video_{timestamp}.mp4"

    # Make sure custom filenames still use the MP4 extension.
    final_filename = Path(filename).with_suffix(".mp4").name

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    mp4_path = VIDEO_DIR / final_filename
    temporary_h264_path = VIDEO_DIR / f"temporary_{timestamp}.h264"

    try:
        # Step 1: Record a raw H.264 video stream.
        subprocess.run(
            [
                "rpicam-vid",
                "-t",
                str(duration_ms),
                "--codec",
                "h264",
                "-o",
                str(temporary_h264_path)
            ],
            check=True
        )

        # Step 2: Package the raw H.264 stream inside an MP4 container.
        #
        # -framerate tells FFmpeg how quickly to display the raw frames.
        # -c:v copy avoids re-encoding, keeping conversion fast.
        # +faststart moves MP4 metadata to the beginning of the file,
        # which helps browsers begin playback sooner.
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-framerate",
                str(VIDEO_FRAME_RATE),
                "-i",
                str(temporary_h264_path),
                "-c:v",
                "copy",
                "-movflags",
                "+faststart",
                str(mp4_path)
            ],
            check=True
        )

    except subprocess.CalledProcessError:
        # Do not return a video path when recording or conversion fails.
        if mp4_path.exists():
            mp4_path.unlink()

        raise

    finally:
        # Remove the temporary raw recording after conversion or failure.
        if temporary_h264_path.exists():
            temporary_h264_path.unlink()

    return mp4_path, timestamp

def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

"""
Block runs when file is executed directly: python src/camera.py
Will later be used to import functions without running this code
"""
if __name__ == "__main__":
    photo_path, photo_timestamp = take_photo()
    print(f"Saved photo to: {photo_path}")
    print(f"Photo timestamp: {photo_timestamp}")

    video_path, video_timestamp = record_video(duration_ms = 5000)
    print(f"Saved video to: {video_path}")
    print(f"Video timestamp: {video_timestamp}")