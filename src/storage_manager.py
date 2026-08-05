"""
storage_manager.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Monitors available storage space and automatically removes the oldest motion
events when storage becomes critically low
"""

import logging
import shutil
from pathlib import Path

from database import (
    delete_event_by_id,
    get_event_count,
    get_oldest_event
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MEDIA_DIR = PROJECT_ROOT / "media"

#Begin cleanup once free storage drops below this percentage.
CLEANUP_START_FREE_PERCENT = 15.0

#Continue deleting events until this much free storage exists.
CLEANUP_STOP_FREE_PERCENT = 25.0

#Never delete below this number of stored events
MINIMUM_EVENTS_TO_KEEP = 10

#Leave enabled while testing.
STORAGE_CLEANUP_DRY_RUN = False

def get_free_storage_percent():
    """
    Calculate the percentage of remaining storage on the SD Card.
    """

    disk_usage = shutil.disk_usage(PROJECT_ROOT)

    if disk_usage.total == 0:
        return 0.0

    return (disk_usage.free / disk_usage.total) * 100

def get_free_storage_bytes():
    """
    Return the number of free bytes on the filesystem
    containing the project.
    """

    return shutil.disk_usage(PROJECT_ROOT).free

def get_safe_media_path(stored_path):
    """
    Convert a database path into a verified media path.

    Returns: Absolute path inside the media directory
    """

    if not stored_path:
        return None

    relative_path = Path(stored_path)

    #Database paths begin with "media/".
    if relative_path.parts and relative_path.parts[0] == "media":
        relative_path = Path(*relative_path.parts[1:])

    resolved_path = (MEDIA_DIR / relative_path).resolve()

    #Prevent accidental deletion outside of the media folder.
    try:
        resolved_path.relative_to(MEDIA_DIR.resolve())
    except ValueError:
        logger.error(
            "Attempted access outside of media directory: %s",
            resolved_path
        )
        return None

    return resolved_path

def delete_media_file(stored_path):
    """
    Delete one stored photo or video.
    """

    media_path = get_safe_media_path(stored_path)

    if media_path is None:
        return

    if not media_path.exists():
        logger.warning(
            "Media file already missing: %s",
            media_path
        )
        return

    media_path.unlink()

    logger.info(
        "Deleted media file: %s",
        media_path
    )

def delete_oldest_event(dry_run=False):
    """
    Delete the oldest complete motion event.

    Removes:
    -Photo
    -Video
    -Database record
    """

    event = get_oldest_event()

    if event is None:
        logger.warning("No events available for cleanup.")
        return False

    event_id = event["id"]

    if dry_run:
        logger.info(
            "Dry Run: Would delete Event #%s",
            event_id
        )
        return True

    logger.warning(
        "Deleting Event #%s to reclaim storage.",
        event_id
    )

    #Delete the media first.
    delete_media_file(event["photo_path"])
    delete_media_file(event["video_path"])

    #Then remove the database record.
    delete_event_by_id(event_id)

    logger.info(
        "Event #%s deleted successfully.",
        event_id
    )

    return True

def cleanup_if_needed(dry_run=STORAGE_CLEANUP_DRY_RUN):
    """
    Check remaining storage and remove old events if necessary.
    """

    free_percent = get_free_storage_percent()

    logger.info(
        "Available storage: %.2f%%",
        free_percent
    )

    #No cleanup needed.
    if free_percent >= CLEANUP_START_FREE_PERCENT:
        logger.info("Storage cleanup not required.")
        return 0

    total_events = get_event_count()

    #Always preserve a small event history.
    if total_events <= MINIMUM_EVENTS_TO_KEEP:
        logger.warning(
            "Cleanup skipped because only %s events remain.",
            total_events
        )
        return 0

    if dry_run:
        logger.warning(
            "Storage cleanup running in DRY RUN mode."
        )

        delete_oldest_event(dry_run=True)

        return 0

    #Record available storage before cleanup begins
    free_bytes_before = get_free_storage_bytes()

    deleted_events = 0

    logger.warning(
        "Beginning automatic storage cleanup."
    )

    #Continue deleting events until sufficient storage has been recovered.
    while get_free_storage_percent() < CLEANUP_STOP_FREE_PERCENT:

        total_events = get_event_count()

        if total_events <= MINIMUM_EVENTS_TO_KEEP:
            logger.warning(
                "Cleanup stopped at minimum event limit."
            )
            break

        if not delete_oldest_event():
            break

        deleted_events += 1

    #Calculate how much physical storage was recovered.
    free_bytes_after = get_free_storage_bytes()
    recovered_bytes = max(0, free_bytes_after - free_bytes_before)
    recovered_megabytes = recovered_bytes / (1024 * 1024)

    logger.info(
        "Cleanup finished. Deleted %s event(s)."
        "Recovered %.2f MB. Available storage is now %.2f%%.",
        deleted_events,
        recovered_megabytes,
        get_free_storage_percent()
    )

    return deleted_events

if __name__ == "__main__":
    from logging_config import setup_logging

    setup_logging()
    cleanup_if_needed()
