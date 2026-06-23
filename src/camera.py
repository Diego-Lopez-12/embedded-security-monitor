import subprocess               #Used to run external programs, execute system commands, and manage new processes directly from code
from pathlib import Path        #For interacting with filesystem paths
from datetime import datetime   #Lets us add timestamps to filenames

#__file__ path to the file: src/camera.py
#parent = src/
#parent.parent = project root folder: embedded-seurity-monitor/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

#Store all camera output in organized project folders
PHOTO_DIR = PROJECT_ROOT / "media" / "photos"
VIDEO_DIR = PROJECT_ROOT / "media" / "videos"

def take_photo(filename: str = None) -> Path:
    """
    Capture an image using the Raspberry Pi Camera

    Args:
        -filename: Name of the photo file to create
    
    Returns:
        -Full path to the saved photo
    """   
    #Use a timestamp to label the jpg
    if filename is None:
        filename = f"photo_{generate_timestamp()}.jpg"

    #Make sure the output folder exists before saving
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

    output_path = PHOTO_DIR / filename

    #Run the Linux Command Used to Take a Photo
    #rpicam-still -o <output_path>
    subprocess.run(["rpicam-still", "-o", str(output_path)], check=True)

    return output_path

def record_video(filename: str = None, duration_ms: int = 5000) -> Path:
    """
    Record a video using the Raspberry Pi Camera

    Args:
        -filename: Name of the video file to create
        -duration_ms: Recording duration in miliseconds

    Returns:
        -Full path to the saved video
    """

    #Use a timestamp to label the video
    if filename is None:
        filename = f"video_{generate_timestamp()}.h264"
    
    #Ensure output folder exists before saving
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    output_path = VIDEO_DIR / filename

    #Run the Linux Command Used to Record a Video
    #rpicam-vid -t <duration_ms> -o <output_path>
    subprocess.run(["rpicam-vid", "-t", str(duration_ms), "-o", str(output_path)], check=True)

    return output_path

def generate_timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

"""
Block runs when file is executed directly: python src/camera.py
Will later be used to import functions without running this code
"""
if __name__ == "__main__":
    photo_path = take_photo()
    print(f"Saved photo to: {photo_path}")

    video_path = record_video(duration_ms = 5000)
    print(f"Saved video to: {video_path}")