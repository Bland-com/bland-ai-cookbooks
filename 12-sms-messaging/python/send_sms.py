"""
Bland AI - Send an SMS Message (Python)

This script sends a single SMS text message using the Bland AI API.
It demonstrates the simplest SMS operation: sending a one-off message
from your Bland phone number to a recipient.

Usage:
    1. Copy .env.example to .env and fill in your API key and phone numbers.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python send_sms.py

The script will:
    - Send a text message to the specified recipient
    - Print the API response showing the delivery status

Note: SMS messaging is an Enterprise feature. Your Bland phone number
must be configured for SMS, and US numbers require A2P 10DLC registration.

Pricing: Each message costs $0.02 (both inbound and outbound).
"""

import os
import sys

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
# This keeps your API key and phone numbers out of source control.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
# It typically starts with "sk-".
API_KEY = os.getenv("BLAND_API_KEY")

# The phone number to send the SMS from. This must be a Bland phone number
# that has been configured for SMS in your Bland dashboard.
FROM_NUMBER = os.getenv("FROM_NUMBER")

# The recipient's phone number in E.164 format (e.g., +15551234567).
# This is the person who will receive your text message.
TO_NUMBER = os.getenv("TO_NUMBER")

# The Bland API base URL. All SMS endpoints are under /v1/sms.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

# Make sure all required environment variables are present before
# making any API calls. This prevents confusing errors later.

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

if not FROM_NUMBER:
    print("Error: FROM_NUMBER is not set.")
    print("Add your SMS-configured Bland phone number to .env (e.g., +15551234567).")
    sys.exit(1)

if not TO_NUMBER:
    print("Error: TO_NUMBER is not set.")
    print("Add the recipient's phone number in E.164 format to .env (e.g., +15551234567).")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Define the message content
# ---------------------------------------------------------------------------

# This is the text message that will be sent to the recipient.
# Keep it clear and concise. Standard SMS messages are limited to
# 160 characters (GSM-7 encoding) or 70 characters (Unicode).
# Longer messages are automatically split into multiple segments
# but still count as a single API message for billing purposes.

MESSAGE = (
    "Hi! This is a test message from Bland AI. "
    "Your SMS integration is working correctly. "
    "Reply to this message to test two-way communication."
)

# ---------------------------------------------------------------------------
# Build the request payload
# ---------------------------------------------------------------------------

# The payload contains all the parameters for the Send SMS endpoint.
# Required fields: phone_number, from, message.
# Optional fields: pathway_id, wait.

payload = {
    # REQUIRED: The recipient's phone number in E.164 format.
    # This is the person who will receive the text message.
    "phone_number": TO_NUMBER,

    # REQUIRED: Your Bland phone number that will appear as the sender.
    # This number must be SMS-configured in your Bland dashboard.
    # It can be the same number you use for voice calls.
    "from": FROM_NUMBER,

    # REQUIRED: The actual text content of the message.
    # This is what the recipient will see on their phone.
    "message": MESSAGE,

    # OPTIONAL: Attach a pathway to drive follow-up conversation logic.
    # If the recipient replies, the pathway will handle the response
    # automatically using your defined conversation flow.
    # Uncomment the line below and replace with your pathway ID to use this.
    # "pathway_id": "your-pathway-id-here",

    # OPTIONAL: If True, the API call will wait for the recipient to reply
    # before returning a response. This is useful for synchronous workflows
    # where you need the reply immediately, but it will block until a
    # response is received (or the request times out).
    # "wait": False,
}

# ---------------------------------------------------------------------------
# Send the SMS
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print("Sending SMS to {}...".format(TO_NUMBER))
print("From: {}".format(FROM_NUMBER))
print("Message: {}".format(MESSAGE))
print()

try:
    # Make the POST request to the Send SMS endpoint.
    # This sends the text message immediately.
    response = requests.post(
        "{}/sms/send".format(BASE_URL),
        json=payload,
        headers=headers,
        timeout=30,  # 30-second timeout for the HTTP request itself
    )

    # Raise an exception for HTTP error codes (4xx, 5xx).
    # This catches issues like invalid API keys (401), bad requests (400),
    # or server errors (500).
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

    # Provide specific guidance for common error codes.
    if response.status_code == 401:
        print()
        print("This usually means your API key is invalid or missing.")
        print("Check that BLAND_API_KEY is correct in your .env file.")
    elif response.status_code == 400:
        print()
        print("This usually means one of the parameters is invalid.")
        print("Check that your phone numbers are in E.164 format")
        print("and that your FROM_NUMBER is SMS-configured.")
    elif response.status_code == 403:
        print()
        print("This may mean SMS is not enabled on your plan.")
        print("SMS is an Enterprise feature. Contact Bland support to enable it.")

    sys.exit(1)

# ---------------------------------------------------------------------------
# Handle the response
# ---------------------------------------------------------------------------

# Parse the JSON response from the API.
data = response.json()

# Print the full response so you can see all the fields returned.
print("SMS sent successfully!")
print()
print("Response from API:")

# Display each field in the response for clarity.
for key, value in data.items():
    print("  {}: {}".format(key, value))

print()
print("The recipient should receive the message within a few seconds.")
print("Each message costs $0.02. Check your Bland dashboard for billing details.")
