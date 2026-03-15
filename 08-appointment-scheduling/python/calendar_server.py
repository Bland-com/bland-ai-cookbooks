"""
Bland AI Cookbook - Calendar Server (Python / Flask)

This is a lightweight calendar server that provides two API endpoints for the
Bland AI scheduling agent to call during a live phone conversation:

    POST /api/availability   - Returns available time slots for a given date
    POST /api/book           - Books an appointment and returns a confirmation

The server uses in-memory storage for demo purposes. All data is lost when
the server restarts. In production, you would replace the in-memory dictionaries
with calls to a real calendar system (Google Calendar, Calendly, Cal.com, etc.).

Usage:
    1. Install dependencies: pip install flask python-dotenv
    2. Run: python calendar_server.py
    3. Server starts on http://localhost:5100
    4. Expose with ngrok: ngrok http 5100

Endpoints:
    POST /api/availability  - Check open slots for a date and service
    POST /api/book          - Book an appointment
    GET  /api/bookings      - List all bookings (for verification)
    GET  /api/health        - Health check
"""

import os
import uuid
import random
from datetime import datetime, timedelta

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from .env file if present.
load_dotenv()

# The port the server listens on. Default is 5100 to avoid conflicts with
# common development servers (3000, 5000, 8000, 8080).
PORT = int(os.getenv("CALENDAR_SERVER_PORT", "5100"))

# The authorization key that tool requests must include. This prevents
# unauthorized access to your calendar endpoints. The Bland AI tool
# sends this in the Authorization header as "Bearer <key>".
AUTH_KEY = os.getenv("CALENDAR_AUTH_KEY", "test-calendar-key")

# ---------------------------------------------------------------------------
# In-memory data store
# ---------------------------------------------------------------------------

# This dictionary holds all booked appointments. In production, this would
# be a database or a call to an external calendar API.
# Structure: { "YYYY-MM-DD": [ { appointment_dict }, ... ] }
booked_appointments = {}

# A list of dental providers. The server randomly assigns a provider to
# each available slot to simulate a multi-provider practice.
PROVIDERS = [
    "Dr. Sarah Chen",
    "Dr. Michael Rodriguez",
    "Dr. Emily Park",
]

# The base time slots offered by the practice. These represent all possible
# appointment times in a day. The availability endpoint removes slots that
# are already booked.
BASE_SLOTS = [
    "8:00 AM",
    "8:30 AM",
    "9:00 AM",
    "9:30 AM",
    "10:00 AM",
    "10:30 AM",
    "11:00 AM",
    "11:30 AM",
    "1:00 PM",
    "1:30 PM",
    "2:00 PM",
    "2:30 PM",
    "3:00 PM",
    "3:30 PM",
    "4:00 PM",
    "4:30 PM",
]

# Duration (in minutes) for each service type. Used for display purposes
# and to calculate appointment end times.
SERVICE_DURATIONS = {
    "cleaning": 45,
    "whitening": 60,
    "exam": 30,
    "filling": 45,
    "crown consultation": 30,
}

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Authentication middleware
# ---------------------------------------------------------------------------

def verify_auth():
    """
    Check that the incoming request has a valid Authorization header.
    The expected format is: "Bearer <AUTH_KEY>"

    Returns None if authentication passes, or a JSON error response
    with a 401 status code if it fails.
    """
    # Get the Authorization header from the request.
    auth_header = request.headers.get("Authorization", "")

    # Extract the token after "Bearer ".
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove the "Bearer " prefix (7 characters)

    # Compare the token to our expected key.
    if token != AUTH_KEY:
        return jsonify({
            "error": "Unauthorized",
            "message": "Invalid or missing Authorization header",
        }), 401

    # Authentication passed. Return None to indicate success.
    return None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_available_slots(date_str, service):
    """
    Calculate available time slots for a given date and service.

    This function starts with all base slots, then removes any that have
    already been booked for the given date. It also simulates realistic
    availability by removing a random subset of slots (to mimic a busy
    practice where some times are already taken by other patients).

    Args:
        date_str (str): The date in YYYY-MM-DD format.
        service (str): The service type requested.

    Returns:
        list: A list of available time slot strings (e.g., ["9:00 AM", "2:00 PM"]).
    """
    # Start with a copy of all possible time slots.
    available = list(BASE_SLOTS)

    # Remove slots that are already booked on this date.
    # Look up all bookings for the given date and remove their time slots.
    existing_bookings = booked_appointments.get(date_str, [])
    for booking in existing_bookings:
        booked_time = booking.get("time")
        if booked_time in available:
            available.remove(booked_time)

    # Simulate a partially booked day by randomly removing some slots.
    # This makes the demo feel more realistic. In production, you would
    # not do this because you would be reading from a real calendar.
    # Use the date string as a seed so the same date always returns the
    # same "random" availability (consistent within a server session).
    seed = hash(date_str + service) % 10000
    rng = random.Random(seed)

    # Remove between 30% and 60% of remaining slots to simulate a busy day.
    num_to_remove = rng.randint(
        int(len(available) * 0.3),
        int(len(available) * 0.6),
    )

    # Shuffle and remove slots. This ensures different slots are removed
    # each time (based on the seed), creating varied but consistent results.
    slots_to_remove = rng.sample(available, min(num_to_remove, len(available)))
    for slot in slots_to_remove:
        available.remove(slot)

    return available


def generate_confirmation_number():
    """
    Generate a human-friendly confirmation number.

    Uses a combination of letters and digits that is easy to read aloud
    over the phone. The format is: BSD-XXXX (where X is a digit).

    Returns:
        str: A confirmation number like "BSD-4829".
    """
    # Generate 4 random digits.
    digits = "".join([str(random.randint(0, 9)) for _ in range(4)])

    # Prefix with "BSD" (Bright Smile Dental) for branding.
    return "BSD-{}".format(digits)


def parse_date(date_str):
    """
    Validate and parse a date string in YYYY-MM-DD format.

    Args:
        date_str (str): The date string to parse.

    Returns:
        datetime or None: A datetime object if valid, None if invalid.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def is_weekday(date_obj):
    """
    Check if a date falls on a weekday (Monday through Friday).

    The dental office is closed on weekends, so we only allow appointments
    on weekdays.

    Args:
        date_obj (datetime): The date to check.

    Returns:
        bool: True if the date is Monday through Friday, False otherwise.
    """
    # weekday() returns 0 for Monday through 6 for Sunday.
    # We want 0 to 4 (Monday to Friday).
    return date_obj.weekday() < 5


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.route("/api/availability", methods=["POST"])
def check_availability():
    """
    POST /api/availability

    Check available appointment slots for a given date and service type.
    This endpoint is called by the Bland AI agent's check_availability tool.

    Expected JSON body:
        {
            "date": "2026-03-20",       (YYYY-MM-DD format)
            "service": "cleaning"        (service type)
        }

    Success response (200):
        {
            "available_slots": ["9:00 AM", "11:30 AM", "2:00 PM"],
            "provider_name": "Dr. Sarah Chen",
            "date": "2026-03-20",
            "service": "cleaning",
            "duration_minutes": 45
        }

    Error responses:
        400 - Missing required fields or invalid date
        401 - Invalid authorization
    """
    # Verify the Authorization header before processing.
    auth_error = verify_auth()
    if auth_error:
        return auth_error

    # Parse the JSON request body.
    body = request.get_json(silent=True) or {}

    # Extract the date and service from the request body.
    date_str = body.get("date", "")
    service = body.get("service", "").lower().strip()

    # Log the incoming request for debugging. This helps you see what the
    # AI agent is sending when you are testing the flow.
    print("\n[AVAILABILITY REQUEST]")
    print("  Date: {}".format(date_str))
    print("  Service: {}".format(service))

    # Validate that both required fields are present.
    if not date_str:
        return jsonify({
            "error": "Missing required field: date",
            "message": "Please provide a date in YYYY-MM-DD format.",
        }), 400

    if not service:
        return jsonify({
            "error": "Missing required field: service",
            "message": "Please provide a service type.",
        }), 400

    # Validate the date format.
    date_obj = parse_date(date_str)
    if not date_obj:
        return jsonify({
            "error": "Invalid date format",
            "message": "Date must be in YYYY-MM-DD format (e.g., 2026-03-20).",
        }), 400

    # Check if the date falls on a weekend.
    if not is_weekday(date_obj):
        day_name = date_obj.strftime("%A")
        return jsonify({
            "available_slots": [],
            "provider_name": "",
            "date": date_str,
            "service": service,
            "message": "Our office is closed on {}s. We are open Monday through Friday.".format(day_name),
        }), 200

    # Look up the service duration. If the service is not recognized, default
    # to 30 minutes but still return results.
    duration = SERVICE_DURATIONS.get(service, 30)

    # Get the available slots for this date and service.
    slots = get_available_slots(date_str, service)

    # Randomly assign a provider for this service on this date.
    # In production, you would look up actual provider schedules.
    provider = random.Random(hash(date_str)).choice(PROVIDERS)

    # Log the response for debugging.
    print("  Available slots: {}".format(slots))
    print("  Provider: {}".format(provider))

    # Return the available slots along with metadata.
    return jsonify({
        # The list of available time slots. The AI agent reads these to
        # the caller so they can pick one.
        "available_slots": slots,

        # The name of the provider assigned to this date. The agent can
        # mention this to make the experience feel more personal.
        "provider_name": provider,

        # Echo back the date and service for confirmation.
        "date": date_str,
        "service": service,

        # The appointment duration in minutes. The agent can share this
        # with the caller if they ask.
        "duration_minutes": duration,
    }), 200


@app.route("/api/book", methods=["POST"])
def book_appointment():
    """
    POST /api/book

    Book an appointment for the caller. This endpoint is called by the
    Bland AI agent's book_appointment tool after the caller has confirmed
    their desired time slot.

    Expected JSON body:
        {
            "date": "2026-03-20",
            "time": "10:00 AM",
            "service": "cleaning",
            "customer_name": "Jane Doe",
            "customer_phone": "+15551234567"
        }

    Success response (200):
        {
            "confirmation_number": "BSD-4829",
            "appointment_time": "10:00 AM on March 20, 2026",
            "provider_name": "Dr. Sarah Chen",
            "service": "cleaning",
            "duration_minutes": 45,
            "customer_name": "Jane Doe",
            "message": "Appointment successfully booked!"
        }

    Error responses:
        400 - Missing required fields, invalid date, or slot already taken
        401 - Invalid authorization
    """
    # Verify the Authorization header before processing.
    auth_error = verify_auth()
    if auth_error:
        return auth_error

    # Parse the JSON request body.
    body = request.get_json(silent=True) or {}

    # Extract all required fields from the request body.
    date_str = body.get("date", "")
    time_str = body.get("time", "")
    service = body.get("service", "").lower().strip()
    customer_name = body.get("customer_name", "")
    customer_phone = body.get("customer_phone", "")

    # Log the incoming booking request for debugging.
    print("\n[BOOKING REQUEST]")
    print("  Date: {}".format(date_str))
    print("  Time: {}".format(time_str))
    print("  Service: {}".format(service))
    print("  Customer: {} ({})".format(customer_name, customer_phone))

    # Validate all required fields are present.
    missing_fields = []
    if not date_str:
        missing_fields.append("date")
    if not time_str:
        missing_fields.append("time")
    if not service:
        missing_fields.append("service")
    if not customer_name:
        missing_fields.append("customer_name")
    if not customer_phone:
        missing_fields.append("customer_phone")

    if missing_fields:
        return jsonify({
            "error": "Missing required fields: {}".format(", ".join(missing_fields)),
            "message": "All fields are required to book an appointment.",
        }), 400

    # Validate the date format.
    date_obj = parse_date(date_str)
    if not date_obj:
        return jsonify({
            "error": "Invalid date format",
            "message": "Date must be in YYYY-MM-DD format.",
        }), 400

    # Check if the date falls on a weekend.
    if not is_weekday(date_obj):
        return jsonify({
            "error": "Office closed",
            "message": "Our office is closed on weekends. Please choose a weekday.",
        }), 400

    # Check if the requested time slot is still available.
    # This prevents double-booking if two callers try to book the same slot
    # at the same time.
    existing_bookings = booked_appointments.get(date_str, [])
    for booking in existing_bookings:
        if booking.get("time") == time_str:
            return jsonify({
                "error": "Slot already booked",
                "message": "Sorry, the {} slot on {} has already been taken. Please choose a different time.".format(
                    time_str, date_str
                ),
            }), 400

    # Generate a unique confirmation number for this appointment.
    confirmation_number = generate_confirmation_number()

    # Assign a provider (consistent with what was shown during availability check).
    provider = random.Random(hash(date_str)).choice(PROVIDERS)

    # Look up the service duration.
    duration = SERVICE_DURATIONS.get(service, 30)

    # Format the appointment time in a human-readable way.
    # Example: "10:00 AM on March 20, 2026"
    formatted_date = date_obj.strftime("%B %d, %Y")
    appointment_time = "{} on {}".format(time_str, formatted_date)

    # Create the appointment record.
    appointment = {
        "confirmation_number": confirmation_number,
        "date": date_str,
        "time": time_str,
        "service": service,
        "duration_minutes": duration,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "provider_name": provider,
        "appointment_time": appointment_time,
        "booked_at": datetime.now().isoformat(),
    }

    # Store the appointment in our in-memory data store.
    # Initialize the date's list if it does not exist yet.
    if date_str not in booked_appointments:
        booked_appointments[date_str] = []
    booked_appointments[date_str].append(appointment)

    # Log the successful booking for debugging.
    print("  Confirmation: {}".format(confirmation_number))
    print("  Provider: {}".format(provider))
    print("  BOOKING CONFIRMED!")

    # Return the confirmation details. The AI agent reads the
    # confirmation_number, appointment_time, and provider_name back
    # to the caller (these are mapped in the tool's "response" field).
    return jsonify({
        # The unique confirmation number. The agent reads this to the
        # caller so they can reference it later.
        "confirmation_number": confirmation_number,

        # A human-readable appointment time string. The agent reads this
        # back to confirm the details.
        "appointment_time": appointment_time,

        # The provider assigned to this appointment.
        "provider_name": provider,

        # Additional details echoed back for completeness.
        "service": service,
        "duration_minutes": duration,
        "customer_name": customer_name,

        # A success message.
        "message": "Appointment successfully booked!",
    }), 200


@app.route("/api/bookings", methods=["GET"])
def list_bookings():
    """
    GET /api/bookings

    List all booked appointments. This endpoint is for verification and
    debugging. After the AI agent books an appointment, you can visit
    this endpoint in your browser to confirm the booking was recorded.

    This endpoint does not require authentication so you can easily
    check it during development.

    Response (200):
        {
            "total_bookings": 3,
            "bookings": [ ... all appointment objects ... ]
        }
    """
    # Flatten all appointments across all dates into a single list.
    all_bookings = []
    for date_str in sorted(booked_appointments.keys()):
        for booking in booked_appointments[date_str]:
            all_bookings.append(booking)

    print("\n[LIST BOOKINGS] Total: {}".format(len(all_bookings)))

    return jsonify({
        "total_bookings": len(all_bookings),
        "bookings": all_bookings,
    }), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    GET /api/health

    A simple health check endpoint. Use this to verify the server is
    running before sending a call.

    Response (200):
        {
            "status": "healthy",
            "server": "Bright Smile Dental Calendar Server",
            "timestamp": "2026-03-14T10:30:00.000000"
        }
    """
    return jsonify({
        "status": "healthy",
        "server": "Bright Smile Dental Calendar Server",
        "timestamp": datetime.now().isoformat(),
    }), 200


# ---------------------------------------------------------------------------
# Start the server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  Bright Smile Dental - Calendar Server")
    print("=" * 60)
    print()
    print("  Server running on http://localhost:{}".format(PORT))
    print()
    print("  Endpoints:")
    print("    POST /api/availability  - Check open time slots")
    print("    POST /api/book          - Book an appointment")
    print("    GET  /api/bookings      - List all bookings")
    print("    GET  /api/health        - Health check")
    print()
    print("  Auth key: {}".format(AUTH_KEY))
    print()
    print("  Next steps:")
    print("    1. Expose this server with ngrok: ngrok http {}".format(PORT))
    print("    2. Copy the ngrok URL to your .env file")
    print("    3. Run scheduling_agent.py to send a call")
    print()
    print("  Waiting for requests...")
    print("=" * 60)
    print()

    # Run the Flask development server.
    # debug=True enables auto-reload when you edit this file.
    # host="0.0.0.0" makes the server accessible from other machines
    # on your network (and from ngrok).
    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=True,
    )
