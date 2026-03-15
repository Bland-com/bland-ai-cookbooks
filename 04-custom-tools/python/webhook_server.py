"""
04 - Custom Tools: Webhook Server (Flask)
==========================================

This is the server that Bland AI calls when your agent triggers a custom
tool during a live phone call. It exposes two endpoints:

  POST /api/book         - Handles appointment booking requests.
  POST /api/crm/lookup   - Handles CRM customer lookup requests.

In a real application, these endpoints would connect to your actual
booking system and CRM database. Here, they use simulated data to
demonstrate the request/response cycle.

How it works:
  1. The agent extracts data from the conversation (date, time, email, etc.).
  2. Bland sends an HTTP POST to the URL configured in your tool schema.
  3. This server processes the request and returns a JSON response.
  4. Bland maps fields from the response to variables (using the JSONPath
     expressions you defined in the tool's "response" field).
  5. The agent uses those variables to continue the conversation.

Usage:
  1. Install dependencies: pip install flask python-dotenv
  2. Run: python webhook_server.py
  3. In a separate terminal, expose the server publicly:
       ngrok http 5000
  4. Copy the ngrok HTTPS URL into your .env file as WEBHOOK_URL.

Security note:
  In production, always validate incoming requests. This example checks
  for a shared secret in the X-Tool-Secret header. In a real deployment,
  you should use a strong, randomly generated secret.
"""

import os
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables (optional for the server, but keeps things
# consistent with the other scripts in this cookbook).
load_dotenv()

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# The shared secret that your tool sends in the X-Tool-Secret header.
# Your server checks this to verify that the request is coming from a
# legitimate source. In production, use a long random string and store
# it in an environment variable.
EXPECTED_SECRET = os.getenv("TOOL_SECRET", "my-shared-secret-123")

# The port the server listens on. Default is 5000.
PORT = int(os.getenv("PORT", "5000"))

# ---------------------------------------------------------------------------
# Simulated data store
#
# In a real application, these would be database queries, API calls to
# your calendar system, CRM lookups, etc.
# ---------------------------------------------------------------------------

# Simulated CRM database. Keyed by email and phone for easy lookup.
CRM_DATABASE = {
    # Lookup by email
    "sarah.jones@example.com": {
        "name": "Sarah Jones",
        "account_id": "ACCT-10042",
        "status": "active",
        "plan": "Premium",
        "since": "2023-06-15"
    },
    "john@example.com": {
        "name": "John Martinez",
        "account_id": "ACCT-10087",
        "status": "active",
        "plan": "Standard",
        "since": "2024-01-20"
    },
    "mike.chen@example.com": {
        "name": "Mike Chen",
        "account_id": "ACCT-10123",
        "status": "past_due",
        "plan": "Premium",
        "since": "2022-11-03"
    },
    # Lookup by phone number
    "+15551234567": {
        "name": "Sarah Jones",
        "account_id": "ACCT-10042",
        "status": "active",
        "plan": "Premium",
        "since": "2023-06-15"
    },
    "+15559876543": {
        "name": "John Martinez",
        "account_id": "ACCT-10087",
        "status": "active",
        "plan": "Standard",
        "since": "2024-01-20"
    }
}


def verify_secret(req):
    """
    Check the X-Tool-Secret header against our expected value.
    Returns True if the secret matches, False otherwise.

    In production, use a timing-safe comparison to prevent timing attacks.
    """
    provided = req.headers.get("X-Tool-Secret", "")
    return provided == EXPECTED_SECRET


# ---------------------------------------------------------------------------
# Endpoint 1: Appointment Booking
# POST /api/book
#
# Expected request body (populated by Bland from the tool's "body" field):
# {
#   "requested_date": "2025-01-15",
#   "requested_time": "14:00",
#   "service_type": "haircut"
# }
#
# Response structure must match the JSONPath expressions in the tool's
# "response" field:
#   "confirmation_number": "$.data.confirmation_id"
#   "appointment_time":    "$.data.scheduled_time"
# ---------------------------------------------------------------------------
@app.route("/api/book", methods=["POST"])
def book_appointment():
    # Verify the shared secret.
    if not verify_secret(request):
        print("[BOOK] Rejected: invalid or missing X-Tool-Secret header.")
        return jsonify({"error": "Unauthorized"}), 401

    # Parse the incoming JSON body.
    body = request.get_json(silent=True) or {}

    # Extract the fields that the agent populated via {{input.property}}.
    requested_date = body.get("requested_date", "unknown")
    requested_time = body.get("requested_time", "unknown")
    service_type = body.get("service_type", "unknown")

    # Log the incoming request so you can verify the data extraction
    # is working correctly during development.
    print()
    print("=" * 60)
    print("[BOOK] Received booking request:")
    print(f"  Date:    {requested_date}")
    print(f"  Time:    {requested_time}")
    print(f"  Service: {service_type}")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # Simulate booking logic.
    #
    # In a real application, you would:
    #   1. Validate the date and time.
    #   2. Check availability in your calendar system.
    #   3. Create the appointment record.
    #   4. Return the real confirmation details.
    #
    # Here we generate a fake confirmation ID and echo back the time.
    # -----------------------------------------------------------------------

    # Generate a unique confirmation ID (APT- prefix + random short UUID).
    confirmation_id = f"APT-{uuid.uuid4().hex[:5].upper()}"

    # Format the scheduled time for a human-friendly response.
    # The agent will read this back to the caller.
    scheduled_time = f"{requested_date} at {requested_time}"

    print(f"[BOOK] Returning confirmation: {confirmation_id}")
    print(f"[BOOK] Scheduled time: {scheduled_time}")
    print()

    # Return the response. The structure must match the JSONPath expressions
    # defined in the tool's "response" mapping:
    #   "confirmation_number": "$.data.confirmation_id"
    #   "appointment_time":    "$.data.scheduled_time"
    #
    # So the response needs a top-level "data" object containing
    # "confirmation_id" and "scheduled_time".
    return jsonify({
        "status": "success",
        "data": {
            "confirmation_id": confirmation_id,
            "scheduled_time": scheduled_time,
            "service": service_type
        }
    })


# ---------------------------------------------------------------------------
# Endpoint 2: CRM Customer Lookup
# POST /api/crm/lookup
#
# Expected request body (populated by Bland from the tool's "body" field):
# {
#   "phone": "+15551234567",
#   "email": "sarah.jones@example.com"
# }
#
# At least one of phone or email should be provided. The agent extracts
# whichever identifier the caller mentioned.
#
# Response structure must match the JSONPath expressions in the tool's
# "response" field:
#   "customer_name":  "$.data.name"
#   "account_status": "$.data.status"
#   "account_id":     "$.data.account_id"
# ---------------------------------------------------------------------------
@app.route("/api/crm/lookup", methods=["POST"])
def crm_lookup():
    # Verify the shared secret.
    if not verify_secret(request):
        print("[CRM] Rejected: invalid or missing X-Tool-Secret header.")
        return jsonify({"error": "Unauthorized"}), 401

    # Parse the incoming JSON body.
    body = request.get_json(silent=True) or {}

    phone = body.get("phone", "").strip()
    email = body.get("email", "").strip()

    print()
    print("=" * 60)
    print("[CRM] Received lookup request:")
    print(f"  Phone: {phone or '(not provided)'}")
    print(f"  Email: {email or '(not provided)'}")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # Look up the customer.
    #
    # Try email first, then phone. In a real application, you would query
    # your database or CRM API (Salesforce, HubSpot, etc.).
    # -----------------------------------------------------------------------
    customer = None

    # Try email lookup.
    if email and email in CRM_DATABASE:
        customer = CRM_DATABASE[email]
        print(f"[CRM] Found customer by email: {customer['name']}")

    # Try phone lookup if email did not match.
    if not customer and phone and phone in CRM_DATABASE:
        customer = CRM_DATABASE[phone]
        print(f"[CRM] Found customer by phone: {customer['name']}")

    # If no customer was found, return an error response.
    # The agent can handle this gracefully if your prompt instructs it to.
    if not customer:
        print("[CRM] No customer found.")
        print()
        return jsonify({
            "status": "not_found",
            "data": {
                "name": "Unknown",
                "account_id": "N/A",
                "status": "not_found"
            }
        })

    print(f"[CRM] Returning account: {customer['account_id']}")
    print(f"[CRM] Status: {customer['status']}")
    print()

    # Return the customer data. The structure matches the JSONPath
    # expressions in the tool's "response" mapping:
    #   "customer_name":  "$.data.name"
    #   "account_status": "$.data.status"
    #   "account_id":     "$.data.account_id"
    return jsonify({
        "status": "success",
        "data": {
            "name": customer["name"],
            "account_id": customer["account_id"],
            "status": customer["status"],
            "plan": customer["plan"],
            "member_since": customer["since"]
        }
    })


# ---------------------------------------------------------------------------
# Health check endpoint.
# GET /
#
# Useful for verifying the server is running. When you set up ngrok, you
# can visit the ngrok URL in your browser to confirm connectivity.
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Bland AI Custom Tools Webhook Server",
        "endpoints": [
            "POST /api/book",
            "POST /api/crm/lookup"
        ],
        "timestamp": datetime.utcnow().isoformat() + "Z"
    })


# ---------------------------------------------------------------------------
# Start the server.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  Bland AI Custom Tools Webhook Server")
    print("=" * 60)
    print()
    print(f"  Listening on port {PORT}")
    print()
    print("  Endpoints:")
    print("    POST /api/book         (appointment booking)")
    print("    POST /api/crm/lookup   (CRM customer lookup)")
    print("    GET  /                 (health check)")
    print()
    print("  Next steps:")
    print(f"    1. In another terminal, run: ngrok http {PORT}")
    print("    2. Copy the HTTPS URL into your .env as WEBHOOK_URL.")
    print("    3. Run create_tool.py or send_call_with_tool.py.")
    print()
    print("  Press Ctrl+C to stop the server.")
    print()

    # debug=True enables auto-reload on code changes during development.
    # Set debug=False in production.
    app.run(host="0.0.0.0", port=PORT, debug=True)
