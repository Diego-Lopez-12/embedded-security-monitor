"""
database.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Handles SQLite database creation and event logging for the monitoring
system. Stores metadata about motion events, including timestamps, photo
paths, video paths, and recording duration.
"""

import sqlite3
from pathlib import Path

#Determine the root directory of the project
#(__file__) points to src/database.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "events.db"

def initialize_database():
    """
    Create the events database and events table if they do
    not already exist.
    """

    #Open a connection to the database
    #If events.db doesn't exist, SQLite auto-creates it
    connection = sqlite3.connect(DATABASE_PATH)

    #Create a cursor object
    #Sends SQL commands to the database
    cursor = connection.cursor()

    #Execute and SQL command that cretes the events table
    #IF NOT EXISTS prevents the table from being recreated
    #each time that the program runs.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            photo_path TEXT,
            video_path TEXT,
            duration_seconds INTEGER
        )
        """)
    
    #Save all changes made during the connection
    connection.commit()

    #Close the database connection
    connection.close()

def add_event(timestamp, photo_path, video_path, duration_seconds):
    """
    Add a new motion event record to the database
    """

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO events (timestamp, photo_path, video_path, duration_seconds)
        VALUES (?, ?, ?, ?)
    """, (timestamp, photo_path, video_path, duration_seconds))

    connection.commit()

    #Save the ID SQLite automatically assigned to this event
    event_id = cursor.lastrowid

    connection.close()

    return event_id

def get_recent_events(limit=10):
    """
    Retrieve the most recent motion events from the database.
    Takes a maximum number of events to return and returns a
    list of database rows ordered from newest to oldest.
    """
    connection = sqlite3.connect(DATABASE_PATH)

    #Return rows that can be accessed by column name.
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, timestamp, photo_path, video_path, duration_seconds
        FROM events
        ORDER BY id DESC
        LIMIT ?
        """, (limit,))

    events = cursor.fetchall()
    connection.close()

    return events

def get_event_by_id(event_id):
    """
    Retrieve one motion event using its database ID.
    Takes the ID of the event to retrieve and returns
    the matching event row, or None if it doesn't exist.
    """
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, timestamp, photo_path, video_path, duration_seconds
        FROM events
        WHERE id = ?
    """, (event_id,))

    event = cursor.fetchone()

    connection.close()

    return event

def get_oldest_event():
    """
    Retrieve the oldest motion event currently stored.

    Returns: The oldest event row, or None if the database is empty
    """

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row    #Access rows by column name

    cursor = connection.cursor()

    #Retrieve oldest event by selecting the lowest ID.
    cursor.execute("""
        SELECT
            id,
            timestamp,
            photo_path,
            video_path,
            duration_seconds
        FROM events
        ORDER by id ASC
        LIMIT 1
    """)

    event = cursor.fetchone()

    connection.close()

    return event

def delete_event_by_id(event_id):
    """
    Delete a motion event from the database.

    Args:
    - event_id: Database ID of the event to remove
    """

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM events
        WHERE id = ?
    """, (event_id,))

    connection.commit()
    connection.close()

def get_event_count():
    """
    Return the total number of event records currently stored.
    """

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM events
    """)

    total_events = cursor.fetchone()[0]
    connection.close()

    return total_events

def get_events_page(page=1, events_per_page=25):
    """
    Retrieve one page of motion events.

    Args:
        page: Page number beginning at 1.
        events_per_page: Number of events shown on each page.

    Returns:
        Event rows ordered from newest to oldest.
    """

    offset = (page - 1) * events_per_page

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            timestamp,
            photo_path,
            video_path,
            duration_seconds
        FROM events
        ORDER BY id DESC
        LIMIT ?
        OFFSET ?
    """, (
        events_per_page,
        offset
    ))

    events = cursor.fetchall()
    connection.close()

    return events



def get_dashboard_statistics():
    """
    Calculate statistics to be used by the Flask dashboard.
    
    Returns a dictionary containing:
     - Total # of Recorded Events
     - Total video recording time
     - Most recent event
    """

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.cursor()

    #COUNT calculates the number of database rows
    #SUM adds all recorded video durations together.
    cursor.execute("""
        SELECT
            COUNT(*) AS total_events,
            COALESCE(SUM(duration_seconds), 0)
                AS total_recording_seconds
            FROM events
    """)

    totals = cursor.fetchone()

    #The highest event ID represents most recently inserted event
    cursor.execute("""
        SELECT
            id,
            timestamp,
            photo_path,
            video_path,
            duration_seconds
        FROM events
        ORDER by id DESC
        LIMIT 1
    """)

    latest_event = cursor.fetchone()

    connection.close()

    return {
        "total_events": totals["total_events"],
        "total_recording_seconds":
            totals["total_recording_seconds"],
        "latest_event": latest_event
    }

if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized at: {DATABASE_PATH}")