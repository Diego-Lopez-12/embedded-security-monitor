"""
web.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Provides the Flask web interface for viewing system
information and recorded motion events.
"""

import math
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    abort,
    render_template,
    request,
    send_from_directory
)

from database import (
    initialize_database,
    get_recent_events,
    get_event_by_id,
    get_event_count,
    get_events_page,
    get_dashboard_statistics
)

#Determine the project directories.
#__file__ points to src/web.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = PROJECT_ROOT / "media"
PHOTO_DIR = MEDIA_DIR / "photos"
VIDEO_DIR = MEDIA_DIR / "videos"

RECENT_EVENT_LIMIT = 10
EVENTS_PER_PAGE = 25

#Create the Flask application object.
#Flask uses this object to register pages, configuration, and routes.
web_app = Flask(__name__)

def get_directory_size(directory):
    """
    Calculate the total size of all files inside a directory.

    Returns:
        Directory size in bytes
    """

    total_bytes = 0

    if not directory.exists():
        return total_bytes
    
    for path in directory.rglob("*"):
        if path.is_file():
            total_bytes += path.stat().st_size

    return total_bytes

def get_media_storage_usage():
    """
    Calculate photo, video, and total media storage usage.

    Returns:
        A  dictionary containing byte counts.
    """

    photo_bytes = get_directory_size(PHOTO_DIR)
    video_bytes = get_directory_size(VIDEO_DIR)

    return {
        "photo_bytes": photo_bytes,
        "video_bytes": video_bytes,
        "total_bytes": photo_bytes + video_bytes
    }

def format_storage_size(size_bytes):
    """
    Convert a byte count into a readable storage measurement.

    Ex:
    1024 Bytes -> 1.00 KB
    """

    size = float(size_bytes)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size_bytes} B"

def format_duration(total_seconds):
    """
    Converts seconds into a readable duration.

    Examples:
    120s -> 2 min
    3670 -> 1 Hr, 1 Min, 10 Sec
    """

    total_seconds = int(total_seconds)

    hours, remaining_seconds = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remaining_seconds, 60)

    duration_parts = []

    if hours:
        label = "hour" if hours == 1 else "hours"
        duration_parts.append(f"{hours} {label}")

    if minutes:
        label = "minute" if minutes == 1 else "minutes"
        duration_parts.append(f"{minutes} {label}")

    if seconds or not duration_parts:
        label = "second" if seconds == 1 else "seconds"
        duration_parts.append(f"{seconds} {label}")

    return " ".join(duration_parts)

def format_event_timestamp(timestamp):
    """
    Convert the stored filename-style timestamp into a format that
    is easier to read.

    Ex:
    2026-07-27_14-35-22
    becomes
    July 27, 2026 at 2:35 PM
    """

    try:
        parsed_timestamp = datetime.strptime(
            timestamp,
            "%Y-%m-%d_%H-%M-%S"
        )

        month = parsed_timestamp.strftime("%B")
        day = parsed_timestamp.day
        year = parsed_timestamp.year
        time = parsed_timestamp.strftime("%I:%M %p").lstrip("0")
    
        return f"{month} {day}, {year} at {time}"
    
    except (TypeError, ValueError):
        #Preserve original value if an older timestamp uses an
        #unexpected format.
        return timestamp

def get_media_file_path(stored_path):
    """
    Convert a database media path into an absolute filesystem path.

    Returns:
        A resolved Path, or None when the path is invalid.
    """

    if not stored_path:
        return None

    relative_path = Path(stored_path)

    # Database paths normally begin with media/.
    if relative_path.parts and relative_path.parts[0] == "media":
        relative_path = Path(*relative_path.parts[1:])

    resolved_path = (MEDIA_DIR / relative_path).resolve()

    # Ensure the resolved file remains inside MEDIA_DIR.
    try:
        resolved_path.relative_to(MEDIA_DIR.resolve())
    except ValueError:
        return None

    return resolved_path

def media_file_exists(stored_path):
    """
    Check whether a database media path points to an existing file.
    """

    media_path = get_media_file_path(stored_path)

    return (
        media_path is not None
        and media_path.is_file()
    )

def prepare_event_for_display(event):
    """
    Convert a SQLite event row into a display-friendly dictionary.
    """

    if event is None:
        return None

    photo_path = event["photo_path"]
    video_path = event["video_path"]

    return {
        "id": event["id"],
        "timestamp": event["timestamp"],
        "formatted_timestamp":
            format_event_timestamp(event["timestamp"]),
        "photo_path": photo_path,
        "video_path": video_path,
        "duration_seconds": event["duration_seconds"],
        "photo_available": media_file_exists(photo_path),
        "video_available": (
            bool(video_path)
            and video_path.lower().endswith(".mp4")
            and media_file_exists(video_path)
        )
    }

@web_app.route("/")
def home():
    """
    Display the dashboard home page
    """

    #Retrieve the ten newest motion events from SQLite. and dashboard statistics
    recent_event_rows = get_recent_events(limit=RECENT_EVENT_LIMIT)
    recent_events = [
        prepare_event_for_display(event)
        for event in recent_event_rows
    ]

    statistics = get_dashboard_statistics()

    latest_event = prepare_event_for_display(statistics["latest_event"])

    storage = get_media_storage_usage()

    #recording_time_display = format_duration(statistics["total_recording_seconds"])

    return render_template(
        "index.html",
        system_status="Online",
        events=recent_events,
        total_events=statistics["total_events"],
        latest_event=latest_event,
        total_recording_time=format_duration(
            statistics["total_recording_seconds"]
        ),
        total_storage=format_storage_size(
            storage["total_bytes"]
        ),
        photo_storage=format_storage_size(
            storage["photo_bytes"]
        ),
        video_storage=format_storage_size(
            storage["video_bytes"]
        )
    )

@web_app.route("/events")
def event_history():
    """
    Display a paginated motion event history.
    """

    requested_page = request.args.get(
        "page",
        default=1,
        type=int
    )

    page = max(requested_page, 1)
    total_events = get_event_count()

    total_pages = max(
        1,
        math.ceil(total_events / EVENTS_PER_PAGE)
    )

    # Prevent page numbers beyond the end of the archive.
    page = min(page, total_pages)

    event_rows = get_events_page(
        page=page,
        events_per_page=EVENTS_PER_PAGE
    )

    events = [
        prepare_event_for_display(event)
        for event in event_rows
    ]

    return render_template(
        "events.html",
        events=events,
        total_events=total_events,
        current_page=page,
        total_pages=total_pages,
        has_previous=page > 1,
        has_next=page < total_pages,
        previous_page=page - 1,
        next_page=page + 1
    )

@web_app.route("/events/<int:event_id>/photo")
def show_photo(event_id):
    """
    Display a page containing the photo for one motion event.
    """

    event_row = get_event_by_id(event_id)

    if event_row is None:
        abort(404)

    event = prepare_event_for_display(event_row)

    photo_filename = None

    if event["photo_path"]:
        photo_filename = Path(event["photo_path"]).name

    return render_template(
        "photo.html",
        event=event,
        photo_filename=photo_filename
    )

@web_app.route("/events/<int:event_id>/video")
def show_video(event_id):
    """
    Display a page containing the video for
    one motion event.
    """

    event_row = get_event_by_id(event_id)
    
    if event_row is None:
        abort(404)

    event = prepare_event_for_display(event_row)

    video_filename = None

    if event["video_path"]:
        video_filename = Path(event["video_path"]).name

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

@web_app.errorhandler(404)
def page_not_found(error):
    """
    Display a styled page when an event or route does not exist.
    """

    return render_template(
        "error.html",
        error_title="Page Not Found",
        error_message=(
            "The requested event or page could not be found."
        )
    ), 404

if __name__ == "__main__":
    #Ensure database and events table exist before Flask Starts
    initialize_database()
    
    #host="0.0.0.0" allows other devices on the local network
    #to reach the server through the Raspberry Pi's IP address.
    web_app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )