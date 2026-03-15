"""
04 - Custom Tools: Create a Saved Tool
=======================================

This script creates a reusable custom tool via the Bland AI Tools API.
Once created, the tool gets a unique tool_id that you can attach to any
future call without redefining the full schema each time.

The example tool here is an "Appointment Booking" tool. When triggered
during a call, the agent will:
  1. Extract a date, time, and service type from the conversation.
  2. Send a POST request to your webhook server with those values.
  3. Speak a filler sentence ("Let me book that for you...") while waiting.
  4. Map the response fields (confirmation number, scheduled time) to
     variables the agent can reference in the rest of the conversation.

Usage:
  1. Copy .env.example to .env and fill in your values.
  2. Run: python create_tool.py
  3. Save the returned tool_id for use in send_call_with_tool.py.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from the .env file in this directory.
# BLAND_API_KEY  : Your Bland AI API key (starts with "sk-").
# WEBHOOK_URL    : The public base URL where your webhook server is reachable.
#                  If you are running locally, use ngrok to create a tunnel
#                  and paste the HTTPS URL here (e.g., https://abc123.ngrok.io).
# ---------------------------------------------------------------------------
load_dotenv()

BLAND_API_KEY = os.getenv("BLAND_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., "https://abc123.ngrok.io"

# Validate that required env vars are present before making any API calls.
if not BLAND_API_KEY:
    print("Error: BLAND_API_KEY is not set in your .env file.")
    sys.exit(1)

if not WEBHOOK_URL:
    print("Error: WEBHOOK_URL is not set in your .env file.")
    print("Start your webhook server, expose it with ngrok, then set the URL.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Define the tool schema.
#
# This is the same structure you would use as an inline tool in the Send Call
# API, but here we are saving it as a standalone, reusable tool.
# ---------------------------------------------------------------------------
tool_schema = {
    # A unique, snake_case name for the tool. The agent references this
    # internally when deciding which tool to invoke.
    "name": "book_appointment",

    # The description is critical. The agent reads this to decide WHEN to use
    # the tool. Be specific about trigger conditions so the agent does not
    # fire the tool at the wrong time.
    "description": (
        "Books an appointment for the caller. Use this tool when the caller "
        "wants to schedule a service such as a haircut, consultation, or "
        "check-up. Do NOT use this tool until the caller has provided a date, "
        "time, and service type."
    ),

    # The full URL that Bland will call when the tool is triggered.
    # We append /api/book to the base webhook URL.
    "url": f"{WEBHOOK_URL}/api/book",

    # The HTTP method for the request. POST is most common for create actions.
    "method": "POST",

    # Headers sent with the request. You can include authentication tokens,
    # content type headers, or any custom headers your server requires.
    "headers": {
        "Content-Type": "application/json",
        # Example: pass a shared secret so your server can verify requests
        # are actually coming from your Bland-configured tool.
        "X-Tool-Secret": "my-shared-secret-123"
    },

    # The request body sent to your endpoint. Use {{input.property}} to
    # inject values that the agent extracted from the conversation. These
    # placeholders correspond to the keys defined in input_schema.properties.
    "body": {
        "requested_date": "{{input.date}}",
        "requested_time": "{{input.time}}",
        "service_type": "{{input.service}}"
    },

    # input_schema defines what data the agent should extract from the
    # conversation before calling your API. It uses JSON Schema conventions.
    "input_schema": {
        # The "example" field is especially important. It shows the agent a
        # sample conversation snippet ("speech") and the expected extracted
        # values. The agent uses this as a reference for format and content.
        "example": {
            "speech": "I'd like to book a haircut for tomorrow at 3 PM.",
            "date": "2025-01-15",
            "time": "15:00",
            "service": "haircut"
        },

        # Top-level type is always "object" for tool inputs.
        "type": "object",

        # Each property defines one field the agent should extract.
        # The "description" tells the agent exactly what format to use.
        "properties": {
            "date": {
                "type": "string",
                "description": (
                    "The requested appointment date in YYYY-MM-DD format. "
                    "Convert relative dates like 'tomorrow' or 'next Monday' "
                    "to absolute dates."
                )
            },
            "time": {
                "type": "string",
                "description": (
                    "The requested appointment time in HH:MM 24-hour format. "
                    "Convert '3 PM' to '15:00', '9 AM' to '09:00', etc."
                )
            },
            "service": {
                "type": "string",
                "description": (
                    "The type of service the caller wants to book, e.g. "
                    "'haircut', 'consultation', 'teeth cleaning', 'oil change'."
                )
            }
        }
    },

    # response maps fields from your API's JSON response to named variables.
    # The syntax uses JSONPath: $.path.to.field
    #
    # After the tool call completes, the agent can reference these variables
    # by name (e.g., "Your confirmation number is {{confirmation_number}}.").
    "response": {
        "confirmation_number": "$.data.confirmation_id",
        "appointment_time": "$.data.scheduled_time"
    },

    # speech is what the agent says out loud while waiting for your API to
    # respond. This prevents awkward silence on the call. Keep it natural
    # and relevant to the action being performed.
    "speech": "Let me book that appointment for you. One moment please."
}

# ---------------------------------------------------------------------------
# Create the tool via the Bland AI Tools API.
# POST https://api.bland.ai/v1/tools
# ---------------------------------------------------------------------------
print("Creating tool: book_appointment")
print(f"Webhook URL: {tool_schema['url']}")
print()

response = requests.post(
    "https://api.bland.ai/v1/tools",
    headers={
        # Bland uses the raw API key directly in the Authorization header.
        # No "Bearer" prefix needed.
        "Authorization": BLAND_API_KEY,
        "Content-Type": "application/json"
    },
    json=tool_schema
)

# ---------------------------------------------------------------------------
# Handle the response.
# On success, you get back a tool_id you can reuse in future calls.
# ---------------------------------------------------------------------------
if response.status_code == 200:
    data = response.json()
    print("Tool created successfully!")
    print(f"Tool ID: {data.get('tool_id', 'N/A')}")
    print(f"Name:    {data.get('name', 'N/A')}")
    print()
    print("Save this tool_id. You can pass it in the 'tools' array when")
    print("sending a call, instead of defining the full schema each time.")
    print()
    print("Full response:")
    print(json.dumps(data, indent=2))
else:
    print(f"Error creating tool (HTTP {response.status_code}):")
    print(response.text)
    sys.exit(1)
