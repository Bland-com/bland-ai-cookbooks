"""
Bland AI - Send Your First Call (Python)

This script sends an outbound phone call using the Bland AI API.
The AI agent acts as a friendly restaurant reservation assistant
for "Bella's Italian Kitchen."

Usage:
    1. Copy .env.example to .env and fill in your API key and phone number.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python send_call.py

The script will:
    - Send a call to the specified phone number
    - Print the call_id for tracking
    - Optionally poll until the call completes and print the result
"""

import os
import sys
import time

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
# This keeps your API key out of source control.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
API_KEY = os.getenv("BLAND_API_KEY")

# The phone number to call, in E.164 format (e.g., +15551234567).
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# The Bland API base URL. All endpoints are under this path.
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

# ---------------------------------------------------------------------------
# Define the agent prompt
# ---------------------------------------------------------------------------

# The "task" is the core instruction set for your AI agent. Think of it as the
# agent's personality, knowledge, and rules all in one prompt. The more
# specific and structured you make this, the better the agent will perform.
#
# Tips for writing great prompts:
#   - Give the agent a clear identity and role.
#   - Specify exactly what information to collect.
#   - Include example phrases and responses for common scenarios.
#   - Define boundaries (what the agent should NOT do).
#   - Use {{variable_name}} syntax to inject dynamic data via request_data.

AGENT_TASK = """You are Bella, a warm and professional reservation assistant for Bella's Italian Kitchen,
a popular Italian restaurant in downtown Chicago.

Your goal is to help the caller make a dinner reservation. You should collect:
1. The number of guests (between 1 and 12; for parties larger than 12, let them know they need to call the events team)
2. The preferred date and time (dinner service runs from 5:00 PM to 10:00 PM, Tuesday through Sunday; closed on Mondays)
3. The name for the reservation
4. Any dietary restrictions or special requests (allergies, high chair needed, birthday celebration, etc.)

Important guidelines:
- Be friendly, warm, and conversational. Use a natural tone, not robotic.
- If someone asks about the menu, mention that you have classic Italian dishes including handmade pasta,
  wood-fired pizza, fresh seafood, and a curated wine list.
- If asked about pricing, mention that entrees range from $18 to $45.
- If the caller wants to speak with a manager or has a complaint, offer to transfer them.
- Confirm all reservation details before ending the call.
- Keep responses concise. One to two sentences at a time works best for phone conversations.

Example greeting: "Hi there! Thank you for calling Bella's Italian Kitchen. I'd love to help you with a reservation.
How many guests will be joining us?"
"""

# ---------------------------------------------------------------------------
# Build the request payload
# ---------------------------------------------------------------------------

# This dictionary contains all the parameters for the API call.
# Required fields are phone_number and task. Everything else is optional
# but helps you fine-tune the agent's behavior.

payload = {
    # REQUIRED: The phone number to call in E.164 format.
    "phone_number": PHONE_NUMBER,

    # REQUIRED: The prompt/instructions that define how the AI agent behaves.
    "task": AGENT_TASK,

    # OPTIONAL: The voice the agent uses on the call.
    # Available voices: "mason", "maya", "ryan", "tina", "josh",
    #                   "florian", "derek", "june", "nat", "paige"
    # Each voice has a distinct tone and personality. Try a few to find
    # the best fit for your use case.
    "voice": "maya",

    # OPTIONAL: The exact first sentence the agent says when the call connects.
    # If omitted, the agent generates its own greeting based on the task prompt.
    # Setting this explicitly ensures a consistent opening every time.
    "first_sentence": (
        "Hi there! Thank you for calling Bella's Italian Kitchen. "
        "I'd love to help you with a reservation. How many guests will be joining us?"
    ),

    # OPTIONAL: Which model to use for generating responses.
    # "base"  - Full-featured model with all capabilities.
    # "turbo" - Lowest latency, but some advanced features may not be available.
    "model": "base",

    # OPTIONAL: The language for the call. Default is "babel-en" (English).
    # Bland supports 40+ languages. Change this if you need a different language.
    "language": "babel-en",

    # OPTIONAL: Maximum call length in minutes. The call automatically ends
    # after this duration. Default is 30 minutes. Set this to prevent
    # unexpectedly long (and expensive) calls.
    "max_duration": 5,

    # OPTIONAL: Whether to record the call. When True, a recording_url will
    # be available in the call details after the call completes.
    "record": True,

    # OPTIONAL: Controls the randomness of the agent's responses.
    # 0.0 = very deterministic and consistent responses.
    # 1.0 = more creative and varied responses.
    # 0.7 is a good balance for most conversational use cases.
    "temperature": 0.7,

    # OPTIONAL: If True, the agent waits silently for the human to speak
    # before saying anything. Useful for inbound-style calls where you want
    # the human to initiate the conversation.
    "wait_for_greeting": False,

    # OPTIONAL: A phone number to transfer the call to if the human asks
    # to speak with a real person. Uncomment and set this if you want to
    # enable live transfers.
    # "transfer_phone_number": "+15559876543",

    # OPTIONAL: A URL that receives a POST request with the full call data
    # when the call completes. Useful for integrating with your backend
    # without needing to poll the API.
    # "webhook": "https://your-server.com/api/bland-webhook",

    # OPTIONAL: Custom key-value pairs that you can reference in the task
    # prompt using {{variable_name}} syntax. Great for personalizing calls.
    # For example, if you set "customer_name": "Sarah" here, you can use
    # {{customer_name}} in the task prompt and it will be replaced with "Sarah".
    "request_data": {
        "restaurant_name": "Bella's Italian Kitchen",
        "location": "downtown Chicago",
    },

    # OPTIONAL: Controls what happens when the call goes to voicemail.
    # "action" can be:
    #   "hangup"        - End the call immediately.
    #   "leave_message" - Leave the specified message.
    #   "ignore"        - Continue as if speaking to a person.
    "voicemail": {
        "action": "leave_message",
        "message": (
            "Hi, this is Bella's Italian Kitchen calling. "
            "We'd love to help you make a reservation. "
            "Please call us back at your convenience. Thank you!"
        ),
    },

    # OPTIONAL: Ambient background audio for the call. Adds a layer of
    # realism to the conversation.
    # Options: null (no background), "office", "cafe", "restaurant", "none"
    "background_track": "restaurant",
}

# ---------------------------------------------------------------------------
# Send the call
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print("Sending call to {}...".format(PHONE_NUMBER))
print()

try:
    # Make the POST request to the Send Call endpoint.
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

except requests.exceptions.HTTPError as e:
    print("Error: API returned status code {}.".format(response.status_code))
    print("Response: {}".format(response.text))
    sys.exit(1)

# Parse the JSON response.
data = response.json()

# Check if the call was successfully queued.
if data.get("status") == "success":
    call_id = data["call_id"]
    print("Call successfully queued!")
    print("Call ID: {}".format(call_id))
    print()
    print("Your phone should ring shortly. Answer it to talk with the AI agent.")
    print()
    print("To retrieve call details after it ends, run:")
    print("  python get_call.py {}".format(call_id))
else:
    # If the status is not "success", print the full response for debugging.
    print("Unexpected response from API:")
    print(data)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Optional: Poll for call completion
# ---------------------------------------------------------------------------

# Uncomment the section below if you want the script to wait for the call
# to finish and then print the results automatically. This is useful for
# testing, but in production you would typically use a webhook instead.

# print("Waiting for call to complete...")
# print("(Press Ctrl+C to stop polling and exit)")
# print()
#
# MAX_POLL_TIME = 300     # Maximum time to poll in seconds (5 minutes)
# POLL_INTERVAL = 5       # Seconds between each poll request
# elapsed = 0
#
# try:
#     while elapsed < MAX_POLL_TIME:
#         # Fetch the current call details.
#         poll_response = requests.get(
#             "{}/calls/{}".format(BASE_URL, call_id),
#             headers=headers,
#             timeout=15,
#         )
#         poll_data = poll_response.json()
#
#         # Check if the call has completed.
#         if poll_data.get("completed"):
#             print("Call completed!")
#             print()
#             print("Duration: {:.1f} minutes".format(poll_data.get("call_length", 0)))
#             print("Answered by: {}".format(poll_data.get("answered_by", "unknown")))
#             print("Cost: ${:.4f}".format(poll_data.get("price", 0)))
#             print()
#
#             # Print the transcript if available.
#             transcript = poll_data.get("concatenated_transcript", "")
#             if transcript:
#                 print("Transcript:")
#                 print("-" * 60)
#                 print(transcript)
#                 print("-" * 60)
#                 print()
#
#             # Print the summary if available.
#             summary = poll_data.get("summary", "")
#             if summary:
#                 print("Summary:")
#                 print(summary)
#                 print()
#
#             break
#
#         # Print a progress dot and wait before polling again.
#         status = poll_data.get("status", "unknown")
#         print("  Status: {} ({}s elapsed)".format(status, elapsed))
#         time.sleep(POLL_INTERVAL)
#         elapsed += POLL_INTERVAL
#
#     else:
#         print("Polling timed out after {} seconds.".format(MAX_POLL_TIME))
#         print("The call may still be in progress. Use get_call.py to check later.")
#
# except KeyboardInterrupt:
#     print()
#     print("Polling stopped. Use get_call.py to check the call later.")
