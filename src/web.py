"""
web.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Provides the Flask web interface for viewing system
information and recorded motion events.
"""

from pathlib import Path

from flask import (
    Flask,
    abort,
    render_template,
    send_from_directory
)

from database import (
    initialize_database,
    get_recent_events,
    get_event_by_id
)

#Determine the project directories.
#__file__ points to src/web.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = PROJECT_ROOT / "media"

#Create the Flask application object.
#Flask uses this object to register pages, configuration, and routes.
web_app = Flask(__name__)

@web_app.route("/")
def home():
    """
    Display the dashboard home page
    """

    #Retrieve the ten newest motion events from SQLite.
    recent_events = get_recent_events(limit=10)

    return render_template(
        "index.html",
        system_status="Online",
        events=recent_events
    )

@web_app.route("/events/<int:event_id>/photo")
def show_photo(event_id):
    """
    Display a page containing the photo for one motion event.
    """

    event = get_event_by_id(event_id)

    if event is None:
        abort(404)

    photo_path = event["photo_path"]

    if not photo_path:
        abort(404)

    photo_filename = Path(photo_path).name

    return render_template(
        "photo.html",
        event=event,
        photo_filename=photo_filename
    )

@web_app.route("/events/<int:event_id>video")
def show_video(event_id):
    """
    Display a page containing the video for
    one motion event.
    """

    event = get_event_by_id(event_id)

    #Return a standard HTTP 404 page if event doesn't exist
    if event is None:
        abort(404)
    
    video_path = event["video_path"]

    #Only MP4 vieos should be displayed in the browser.
    if not video_path or not video_path.lower().endswith(".mp4"):
        abort(404)
    
    video_filename = Path(video_path).name

    return render_template(
        "video.html",
        event=event,
        video_filename=video_filename
    )

@web_app.route("/media/<path:filename>")
def serve_media(filename):
    """
    Serve recorded photos and videos from the project's media folder.

    The database stores pahts such as:
        media/photos/photo_2026-07-20_14-26-34.jpg

    The HTML removes the leading 'media/' poriton before requesting
    the file from this route.
    """

    return send_from_directory(
        MEDIA_DIR,
        filename,
        conditional=True
    )

if __name__ == "__main__":
    #Ensure database and events table exist before Flask Starts
    initialize_database()
    
    #host="0.0.0.0" allows other devices on the local network
    #to reach the server through the Raspberry Pi's IP address.
    web_app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )