"""
web.py

Author: Diego Lopez
Project: Embedded Security Monitoring System

Description:
Provides the Flask web interface for viewing system
information and recorded motion events.
"""

from flask import Flask, render_template
from database import initialize_database, get_recent_events

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