"""
04 - Custom Tools: Send a Call with Inline Tools
=================================================

This script sends an outbound phone call with two custom tools attached
directly in the request payload (the "inline" approach). The agent can
invoke either tool during the conversation based on what the caller says.

Tool 1: book_appointment
  Extracts a date, time, and service from conversation, sends them to
  your webhook server's /api/book endpoint, and reads back a confirmation.

Tool 2: crm_lookup
  Extracts a phone number or email from conversation, sends it to your
  webhook server's /api/crm/lookup endpoint, and retrieves the customer's
  name and account details so the agent can personalize the call.

Usage:
  1. Make sure your webhook server is running (python webhook_server.py).
  2. Make sure it is publicly accessible (e.g., via ngrok).
  3. Copy .env.example to .env and fill in your values.
  4. Run: python send_call_with_tool.py
  5. Answer the phone and test both tools by saying things like:
     - "I want to book a consultation for Friday at 10 AM."
     - "Can you look up my account? My email is sarah@example.com."
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables.
# ---------------------------------------------------------------------------
load_dotenv()

BLAND_API_KEY = os.getenv("BLAND_API_KEY")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")    # The number to call (yours for testing)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")      # Your public webhook base URL

# Validate required variables.
if not BLAND_API_KEY:
    print("Error: BLAND_API_KEY is not set in your .env file.")
    sys.exit(1)

if not PHONE_NUMBER:
    print("Error: PHONE_NUMBER is not set in your .env file.")
    print("Set it to a real phone number in E.164 format, e.g., +15551234567")
    sys.exit(1)

if not WEBHOOK_URL:
    print("Error: WEBHOOK_URL is not set in your .env file.")
    print("Start your webhook server, expose it with ngrok, then set the URL.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Tool 1: Appointment Booking
#
# This tool fires when the caller asks to schedule something. The agent
# extracts the date, time, and service, sends them to your /api/book
# endpoint, and maps the response so it can read back a confirmation.
# ---------------------------------------------------------------------------
appointment_tool = {
    "name": "book_appointment",

    "description": (
        "Books an appointment for the caller. Use this when the caller wants "
        "to schedule any kind of service, such as a haircut, consultation, "
        "dental cleaning, or car service. Only trigger this after the caller "
        "has provided a date, time, and service type."
    ),

    "url": f"{WEBHOOK_URL}/api/book",
    "method": "POST",

    "headers": {
        "Content-Type": "application/json",
        "X-Tool-Secret": "my-shared-secret-123"
    },

    # The body uses {{input.property}} placeholders. These get replaced
    # with the values the agent extracted from the conversation.
    "body": {
        "requested_date": "{{input.date}}",
        "requested_time": "{{input.time}}",
        "service_type": "{{input.service}}"
    },

    "input_schema": {
        "example": {
            "speech": "I'd like to book a teeth cleaning for next Wednesday at 2 PM.",
            "date": "2025-01-22",
            "time": "14:00",
            "service": "teeth cleaning"
        },
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": (
                    "The desired appointment date in YYYY-MM-DD format. "
                    "Convert relative references like 'tomorrow' or "
                    "'next Friday' into absolute dates."
                )
            },
            "time": {
                "type": "string",
                "description": (
                    "The desired appointment time in HH:MM 24-hour format. "
                    "For example, '2 PM' becomes '14:00'."
                )
            },
            "service": {
                "type": "string",
                "description": (
                    "The type of service to book. Examples: 'haircut', "
                    "'consultation', 'teeth cleaning', 'oil change'."
                )
            }
        }
    },

    # Map your API response fields to agent-accessible variables.
    # After the tool call, the agent can say:
    #   "Your confirmation number is {{confirmation_number}}."
    "response": {
        "confirmation_number": "$.data.confirmation_id",
        "appointment_time": "$.data.scheduled_time"
    },

    # Filler speech while the API request is in flight.
    "speech": "Let me check our availability and book that for you. One moment."
}

# ---------------------------------------------------------------------------
# Tool 2: CRM Lookup
#
# This tool fires when the caller wants to check their account or the agent
# needs customer details. The agent extracts an email or phone number, sends
# it to /api/crm/lookup, and gets back the customer's name, status, and
# account ID so it can personalize the rest of the call.
# ---------------------------------------------------------------------------
crm_lookup_tool = {
    "name": "crm_lookup",

    "description": (
        "Looks up a customer's account by their phone number or email address. "
        "Use this when the caller asks about their account, wants to check an "
        "order status, or needs billing information. Also use this at the start "
        "of the call if the caller identifies themselves with an email or phone."
    ),

    "url": f"{WEBHOOK_URL}/api/crm/lookup",
    "method": "POST",

    "headers": {
        "Content-Type": "application/json",
        "X-Tool-Secret": "my-shared-secret-123"
    },

    # The body sends whichever identifier the agent was able to extract.
    # If the caller only gives a phone number, the email field may be empty.
    "body": {
        "phone": "{{input.phone}}",
        "email": "{{input.email}}"
    },

    "input_schema": {
        "example": {
            "speech": "Sure, my email is sarah.jones@example.com.",
            "phone": "",
            "email": "sarah.jones@example.com"
        },
        "type": "object",
        "properties": {
            "phone": {
                "type": "string",
                "description": (
                    "The customer's phone number. Use E.164 format if "
                    "possible (e.g., +15551234567). Leave empty if the "
                    "caller only provided an email."
                )
            },
            "email": {
                "type": "string",
                "description": (
                    "The customer's email address. Leave empty if the "
                    "caller only provided a phone number."
                )
            }
        }
    },

    # Map CRM response fields to named variables the agent can use.
    "response": {
        "customer_name": "$.data.name",
        "account_status": "$.data.status",
        "account_id": "$.data.account_id"
    },

    "speech": "I'm pulling up your account now. Just a moment."
}

# ---------------------------------------------------------------------------
# Build the call payload.
#
# The "tools" array holds both tool definitions inline. You could also pass
# a tool_id string (from create_tool.py) instead of the full object.
#
# The "task" prompt tells the agent how to behave and, importantly,
# instructs it to confirm details after using each tool.
# ---------------------------------------------------------------------------
call_payload = {
    # The phone number to call, in E.164 format.
    "phone_number": PHONE_NUMBER,

    # The agent's instructions. This prompt controls the agent's personality,
    # behavior, and how it handles tool results. Notice the instructions
    # about reading back confirmation numbers and customer details.
    "task": (
        "You are a friendly and efficient customer service agent for "
        "Sunrise Services, a multi-purpose service company. Your job is "
        "to help callers book appointments and look up their accounts.\n\n"
        "Key behaviors:\n"
        "- Greet the caller warmly and ask how you can help.\n"
        "- If they want to book an appointment, ask for the service type, "
        "preferred date, and preferred time before using the booking tool.\n"
        "- After booking, always read back the confirmation number and "
        "scheduled time so the caller can write it down.\n"
        "- If they ask about their account, ask for their email or phone "
        "number, then use the CRM lookup tool.\n"
        "- After looking up their account, greet them by name and share "
        "their account status.\n"
        "- Be concise and professional, but friendly.\n"
        "- If a tool call fails, apologize and offer to try again or "
        "transfer the caller to a human agent."
    ),

    # First sentence the agent says when the call connects.
    "first_sentence": (
        "Hi there! Thank you for calling Sunrise Services. "
        "How can I help you today?"
    ),

    # Voice selection. See cookbook 11 for all available voices.
    "voice": "mason",

    # Record the call so you can review the transcript afterward.
    "record": True,

    # Maximum call duration in minutes.
    "max_duration": 10,

    # The tools array: both tools are defined inline here.
    # You could also mix inline tools with saved tool IDs, e.g.:
    #   "tools": [appointment_tool, "saved-tool-id-here"]
    "tools": [
        appointment_tool,
        crm_lookup_tool
    ]
}

# ---------------------------------------------------------------------------
# Send the call via the Bland AI API.
# POST https://api.bland.ai/v1/calls
# ---------------------------------------------------------------------------
print("Sending call with 2 custom tools attached:")
print(f"  1. book_appointment -> {WEBHOOK_URL}/api/book")
print(f"  2. crm_lookup       -> {WEBHOOK_URL}/api/crm/lookup")
print(f"  Phone: {PHONE_NUMBER}")
print()

response = requests.post(
    "https://api.bland.ai/v1/calls",
    headers={
        "Authorization": BLAND_API_KEY,
        "Content-Type": "application/json"
    },
    json=call_payload
)

# ---------------------------------------------------------------------------
# Handle the response.
# ---------------------------------------------------------------------------
if response.status_code == 200:
    data = response.json()
    call_id = data.get("call_id", "N/A")

    print("Call successfully queued!")
    print(f"Call ID: {call_id}")
    print()
    print("Your phone should ring shortly. Try these prompts:")
    print('  - "I want to book a haircut for tomorrow at 3 PM."')
    print('  - "Can you look up my account? My email is john@example.com."')
    print()
    print("Watch your webhook server logs to see the incoming tool requests.")
    print()
    print(f"After the call, retrieve details with:")
    print(f"  curl -H 'Authorization: {BLAND_API_KEY}' "
          f"https://api.bland.ai/v1/calls/{call_id}")
else:
    print(f"Error sending call (HTTP {response.status_code}):")
    print(response.text)
    sys.exit(1)
