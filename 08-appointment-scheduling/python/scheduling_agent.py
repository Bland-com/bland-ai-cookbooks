"""
Bland AI Cookbook - Appointment Scheduling Agent (Python)

This script sends an outbound phone call using the Bland AI API with two
custom tools attached: check_availability and book_appointment. During the
call, the AI agent uses these tools to query a calendar server for open
time slots and then book the caller's chosen appointment.

Usage:
    1. Start the calendar server first: python calendar_server.py
    2. Expose the server with ngrok: ngrok http 5100
    3. Copy .env.example to .env and fill in your values.
    4. Install dependencies: pip install requests python-dotenv
    5. Run: python scheduling_agent.py

The script will:
    - Build two custom tool definitions (check_availability, book_appointment)
    - Send a call to the specified phone number with those tools attached
    - Print the call_id for tracking
"""

import os
import sys

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
# This keeps sensitive values like API keys out of source control.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
# This authenticates every request to the Bland API.
API_KEY = os.getenv("BLAND_API_KEY")

# The phone number to call, in E.164 format (e.g., +15551234567).
# This is the number the AI agent will dial.
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# The public URL of your calendar server. During local development, this is
# your ngrok forwarding URL (e.g., https://abc123.ngrok-free.app).
# In production, this would be your actual server URL.
CALENDAR_SERVER_URL = os.getenv("CALENDAR_SERVER_URL", "http://localhost:5100")

# An authorization key for your calendar server. This is sent in the
# Authorization header of every tool request to verify the call is legitimate.
# Set this to any string you choose, and make sure it matches what your
# calendar server expects.
CALENDAR_AUTH_KEY = os.getenv("CALENDAR_AUTH_KEY", "test-calendar-key")

# The Bland API base URL. All Bland endpoints live under this path.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

if not PHONE_NUMBER:
    print("Error: PHONE_NUMBER is not set.")
    print("Add your phone number in E.164 format to .env (e.g., +15551234567).")
    sys.exit(1)

if CALENDAR_SERVER_URL == "http://localhost:5100":
    print("Warning: CALENDAR_SERVER_URL is set to localhost.")
    print("Bland's servers cannot reach localhost. Use ngrok to create a")
    print("public URL and set CALENDAR_SERVER_URL in your .env file.")
    print()

# ---------------------------------------------------------------------------
# Define the agent prompt
# ---------------------------------------------------------------------------

# The "task" is the core instruction set for the AI agent. It defines the
# agent's identity, behavior, and rules. The more specific you are, the
# better the agent performs.
#
# This prompt is for a dental office called "Bright Smile Dental." You can
# adapt it for any business (salon, spa, mechanic, etc.) by changing the
# business name, services, and hours.
#
# Key elements of a good scheduling prompt:
#   - Clear identity and role for the agent
#   - The list of services the business offers
#   - Business hours so the agent can guide callers to valid times
#   - Instructions on when to use each tool
#   - How to handle edge cases (no availability, rescheduling, etc.)
#   - A natural, conversational tone

AGENT_TASK = """You are Emma, a friendly and professional receptionist at Bright Smile Dental,
a family dental practice located at 450 Oak Avenue in Springfield.

Your job is to help callers schedule dental appointments. Here is how you should handle the call:

1. Greet the caller warmly and ask what type of service they need.
2. Our available services are:
   - Cleaning (45 minutes, $120)
   - Whitening (60 minutes, $250)
   - Exam (30 minutes, $95)
   - Filling (45 minutes, $180)
   - Crown consultation (30 minutes, $150)
3. Once you know the service, ask the caller what date works best for them.
4. Use the check_availability tool to look up open time slots for that date and service.
5. Read the available times to the caller in a natural way. For example: "I have openings at
   9:00 AM, 11:30 AM, and 2:00 PM. Which of those works best for you?"
6. If there are no available slots on that date, apologize and suggest they try a different day.
   Offer to check another date for them.
7. Once the caller picks a time, confirm the details: the service, date, and time.
8. Ask for their full name if you do not already have it.
9. Use the book_appointment tool to finalize the booking. The customer_phone field should be
   the phone number they are calling from.
10. Read back the confirmation number and appointment details so the caller can write them down.

Important guidelines:
- Be warm, friendly, and reassuring. Many people are nervous about dental visits.
- Keep responses concise. One to two sentences at a time works best on the phone.
- Our office hours are Monday through Friday, 8:00 AM to 5:00 PM. We are closed on weekends.
- If a caller asks about pricing, share the prices listed above.
- If a caller wants to cancel or reschedule an existing appointment, let them know they can
  call back during business hours to speak with the front desk staff.
- If a caller has a dental emergency, advise them to go to the nearest emergency room or
  call our emergency line at (555) 911-2345.
- Do not make up availability. Always use the check_availability tool to get real data.
- Do not book an appointment without the caller's explicit confirmation of the time slot.
"""

# ---------------------------------------------------------------------------
# Define the custom tools
# ---------------------------------------------------------------------------

# Custom tools let the AI agent make HTTP requests to your server during the
# conversation. The agent reads each tool's "description" to decide when to
# use it, extracts the required input fields from the conversation, calls
# your endpoint, and then uses the response data in its next reply.

# Tool 1: check_availability
# This tool queries your calendar server for open time slots on a given date
# for a specific service. The agent calls this when the caller mentions a
# date or asks about availability.
check_availability_tool = {
    # A unique identifier for this tool. The AI references this internally.
    # Use lowercase with underscores.
    "name": "check_availability",

    # A human-readable description that tells the AI WHEN to use this tool.
    # The model reads this to decide if the tool is relevant to the current
    # point in the conversation. Be specific and descriptive.
    "description": "Check available appointment slots for a given date and service type",

    # The endpoint URL the tool sends its request to. This must be publicly
    # accessible. During local development, use your ngrok URL.
    "url": "{}/api/availability".format(CALENDAR_SERVER_URL),

    # The HTTP method for the request. POST is typical for tools that send data.
    "method": "POST",

    # HTTP headers sent with every request from this tool. Include
    # authentication and content type here.
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(CALENDAR_AUTH_KEY),
    },

    # The JSON body sent to your server. Values wrapped in {{input.field}}
    # are filled in dynamically by the AI based on what the caller said.
    # For example, if the caller says "next Tuesday," the AI converts that
    # to a YYYY-MM-DD date string and inserts it into {{input.date}}.
    "body": {
        "date": "{{input.date}}",
        "service": "{{input.service}}",
    },

    # Describes the parameters the AI needs to extract from the conversation
    # before calling this tool. The "example" field shows the model what
    # valid values look like. The "properties" object describes each field's
    # type and meaning so the model can extract them accurately.
    "input_schema": {
        "example": {
            "date": "2026-03-15",
            "service": "cleaning",
        },
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "The date to check in YYYY-MM-DD format",
            },
            "service": {
                "type": "string",
                "description": "The type of service requested (cleaning, whitening, exam, filling, or crown consultation)",
            },
        },
    },

    # Maps fields from your server's JSON response to variables the AI can
    # use in its next reply. Uses JSONPath syntax ($.field_name) to extract
    # values from the response body.
    # After this tool runs, the AI can reference "available_slots" and
    # "provider_name" when speaking to the caller.
    "response": {
        "available_slots": "$.available_slots",
        "provider_name": "$.provider_name",
    },

    # What the agent says to the caller WHILE the HTTP request is in flight.
    # This fills the brief silence during the API call so the conversation
    # feels natural. Keep it short and conversational.
    "speech": "Let me check what times are available for you.",
}

# Tool 2: book_appointment
# This tool sends a booking request to your calendar server with all the
# appointment details. The agent calls this after the caller has confirmed
# their desired time slot.
book_appointment_tool = {
    # Unique identifier for this tool.
    "name": "book_appointment",

    # Description that tells the AI when to use this tool. The model will
    # only trigger this after the caller has confirmed a specific slot.
    "description": "Book an appointment for the caller at a specific date, time, and service",

    # The booking endpoint on your calendar server.
    "url": "{}/api/book".format(CALENDAR_SERVER_URL),

    # HTTP method for the request.
    "method": "POST",

    # Headers for authentication and content type.
    "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(CALENDAR_AUTH_KEY),
    },

    # The JSON body for the booking request. The AI fills in all five fields
    # from the conversation. It will ask the caller for any missing
    # information (like their name) before triggering this tool.
    "body": {
        "date": "{{input.date}}",
        "time": "{{input.time}}",
        "service": "{{input.service}}",
        "customer_name": "{{input.customer_name}}",
        "customer_phone": "{{input.customer_phone}}",
    },

    # Input schema with all five required fields. The AI extracts each one
    # from the conversation context. The "example" helps the model
    # understand the expected format for each field.
    "input_schema": {
        "example": {
            "date": "2026-03-15",
            "time": "10:00 AM",
            "service": "cleaning",
            "customer_name": "John Smith",
            "customer_phone": "+15551234567",
        },
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "Appointment date in YYYY-MM-DD format",
            },
            "time": {
                "type": "string",
                "description": "Appointment time like '10:00 AM'",
            },
            "service": {
                "type": "string",
                "description": "Service type (cleaning, whitening, exam, filling, or crown consultation)",
            },
            "customer_name": {
                "type": "string",
                "description": "Customer's full name",
            },
            "customer_phone": {
                "type": "string",
                "description": "Customer's phone number in E.164 format",
            },
        },
    },

    # Maps the booking confirmation response to variables the AI can read
    # back to the caller. After booking, the agent tells the caller their
    # confirmation number, appointment time, and provider name.
    "response": {
        "confirmation_number": "$.confirmation_number",
        "appointment_time": "$.appointment_time",
        "provider_name": "$.provider_name",
    },

    # What the agent says while the booking request is being processed.
    "speech": "Perfect, I am booking that for you right now.",
}

# ---------------------------------------------------------------------------
# Build the request payload
# ---------------------------------------------------------------------------

# This dictionary contains all the parameters for the Bland API call.
# The "tools" array is the key addition compared to a basic call. It tells
# the agent what external actions it can take during the conversation.

payload = {
    # REQUIRED: The phone number to call in E.164 format.
    "phone_number": PHONE_NUMBER,

    # REQUIRED: The prompt/instructions that define how the AI agent behaves.
    # This is the dental receptionist prompt defined above.
    "task": AGENT_TASK,

    # REQUIRED FOR THIS COOKBOOK: The array of custom tools the agent can use.
    # Each tool is a dictionary with name, description, url, method, headers,
    # body, input_schema, response, and speech fields.
    "tools": [
        check_availability_tool,
        book_appointment_tool,
    ],

    # OPTIONAL: The voice the agent uses on the call.
    # Available voices: "mason", "maya", "ryan", "tina", "josh",
    #                   "florian", "derek", "june", "nat", "paige"
    # "maya" has a warm, professional tone that works well for healthcare.
    "voice": "maya",

    # OPTIONAL: The exact first sentence the agent says when the call connects.
    # Setting this explicitly ensures a consistent greeting every time.
    "first_sentence": (
        "Hi there! Thank you for calling Bright Smile Dental. "
        "This is Emma. How can I help you today?"
    ),

    # OPTIONAL: Which model to use for generating responses.
    # "base" is the full-featured model that supports all tool capabilities.
    "model": "base",

    # OPTIONAL: Maximum call length in minutes. Prevents unexpectedly long
    # calls. 10 minutes is plenty for a scheduling conversation.
    "max_duration": 10,

    # OPTIONAL: Whether to record the call. Set to True so you can review
    # the conversation and verify tool usage after the call.
    "record": True,

    # OPTIONAL: Controls the randomness of responses.
    # 0.0 = very deterministic. 1.0 = very creative.
    # 0.7 is a good default for natural conversation.
    "temperature": 0.7,

    # OPTIONAL: If True, the agent waits for the caller to speak first.
    # Set to False for outbound calls so the agent greets immediately.
    "wait_for_greeting": False,

    # OPTIONAL: Custom key-value pairs accessible in the prompt using
    # {{variable_name}} syntax. Useful for personalizing each call.
    "request_data": {
        "office_name": "Bright Smile Dental",
        "office_address": "450 Oak Avenue, Springfield",
        "office_phone": "(555) 234-5678",
    },

    # OPTIONAL: Ambient background audio. "office" adds subtle office
    # sounds that make the call feel like a real receptionist.
    "background_track": "office",

    # OPTIONAL: Voicemail handling. If the call goes to voicemail, leave a
    # message asking the person to call back.
    "voicemail": {
        "action": "leave_message",
        "message": (
            "Hi, this is Emma from Bright Smile Dental. "
            "We were calling to help you schedule an appointment. "
            "Please call us back at (555) 234-5678 at your convenience. "
            "Thank you and have a great day!"
        ),
    },
}

# ---------------------------------------------------------------------------
# Send the call
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed for the Bland API).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print("Sending scheduling call to {}...".format(PHONE_NUMBER))
print("Calendar server: {}".format(CALENDAR_SERVER_URL))
print("Tools attached: check_availability, book_appointment")
print()

try:
    # Make the POST request to the Send Call endpoint.
    # The tools array is included in the payload, which tells the agent
    # what external actions it can perform during the conversation.
    response = requests.post(
        "{}/calls".format(BASE_URL),
        json=payload,
        headers=headers,
        timeout=30,  # 30-second timeout for the HTTP request itself
    )

    # Raise an exception for HTTP error codes (4xx, 5xx).
    response.raise_for_status()

except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the Bland API.")
    print("Check your internet connection and try again.")
    sys.exit(1)

except requests.exceptions.Timeout:
    print("Error: The request timed out.")
    print("The Bland API may be experiencing high traffic. Try again in a moment.")
    sys.exit(1)

except requests.exceptions.HTTPError:
    print("Error: API returned status code {}.".format(response.status_code))
    print("Response: {}".format(response.text))
    sys.exit(1)

# Parse the JSON response from Bland.
data = response.json()

# Check if the call was successfully queued.
if data.get("status") == "success":
    call_id = data["call_id"]
    print("Call successfully queued!")
    print("Call ID: {}".format(call_id))
    print()
    print("Your phone should ring shortly. Answer it and try booking an appointment.")
    print()
    print("Watch your calendar server terminal to see tool requests come in.")
    print()
    print("To retrieve call details after it ends, run:")
    print("  curl -X GET https://api.bland.ai/v1/calls/{} \\".format(call_id))
    print("    -H 'Authorization: {}'".format(API_KEY))
else:
    # If the status is not "success", print the full response for debugging.
    print("Unexpected response from API:")
    print(data)
    sys.exit(1)
