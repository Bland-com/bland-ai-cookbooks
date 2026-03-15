"""
Bland AI - Get Call Details (Python)

This script retrieves the details of a completed call using the Bland AI API.
It prints the transcript, summary, duration, cost, and other metadata.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python get_call.py <call_id>

The call_id is printed by send_call.py when you send a call.
You can also find call IDs in the Bland dashboard under the Calls tab.
"""

import os
import sys
import json

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from .env file.
load_dotenv()

# Your Bland API key.
API_KEY = os.getenv("BLAND_API_KEY")

# The Bland API base URL.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate inputs
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

# The call_id should be passed as a command-line argument.
# Example: python get_call.py abc12345-def6-7890-ghij-klmnopqrstuv
if len(sys.argv) < 2:
    print("Usage: python get_call.py <call_id>")
    print()
    print("The call_id is returned by send_call.py when you send a call.")
    print("Example: python get_call.py abc12345-def6-7890-ghij-klmnopqrstuv")
    sys.exit(1)

call_id = sys.argv[1]

# ---------------------------------------------------------------------------
# Fetch call details
# ---------------------------------------------------------------------------

# Set the authorization header.
headers = {
    "Authorization": API_KEY,
}

print("Fetching details for call: {}".format(call_id))
print()

try:
    # Make the GET request to the call details endpoint.
    # The call_id is included directly in the URL path.
    response = requests.get(
        "{}/calls/{}".format(BASE_URL, call_id),
        headers=headers,
        timeout=15,
    )

    # Raise an exception for HTTP error codes.
    response.raise_for_status()

except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the Bland API.")
    print("Check your internet connection and try again.")
    sys.exit(1)

except requests.exceptions.Timeout:
    print("Error: The request timed out. Try again in a moment.")
    sys.exit(1)

except requests.exceptions.HTTPError:
    print("Error: API returned status code {}.".format(response.status_code))
    if response.status_code == 404:
        print("Call not found. Double check the call_id.")
    elif response.status_code == 401:
        print("Invalid API key. Check your .env file.")
    else:
        print("Response: {}".format(response.text))
    sys.exit(1)

# Parse the JSON response.
data = response.json()

# ---------------------------------------------------------------------------
# Display call metadata
# ---------------------------------------------------------------------------

print("=" * 60)
print("CALL DETAILS")
print("=" * 60)
print()

# Basic call information.
print("Call ID:       {}".format(data.get("call_id", "N/A")))
print("Status:        {}".format(data.get("status", "N/A")))
print("Completed:     {}".format(data.get("completed", "N/A")))
print("Queue Status:  {}".format(data.get("queue_status", "N/A")))
print()

# Phone numbers involved in the call.
print("To:            {}".format(data.get("to", "N/A")))
print("From:          {}".format(data.get("from", "N/A")))
print("Answered By:   {}".format(data.get("answered_by", "N/A")))
print()

# Call duration and cost.
call_length = data.get("call_length")
if call_length is not None:
    print("Duration:      {:.1f} minutes".format(call_length))
else:
    print("Duration:      N/A")

price = data.get("price")
if price is not None:
    print("Cost:          ${:.4f}".format(price))
else:
    print("Cost:          N/A")

print()

# ---------------------------------------------------------------------------
# Display error information (if any)
# ---------------------------------------------------------------------------

error_message = data.get("error_message")
if error_message:
    print("=" * 60)
    print("ERROR")
    print("=" * 60)
    print(error_message)
    print()

# ---------------------------------------------------------------------------
# Display the recording URL (if recording was enabled)
# ---------------------------------------------------------------------------

recording_url = data.get("recording_url")
if recording_url:
    print("Recording URL: {}".format(recording_url))
    print()

# ---------------------------------------------------------------------------
# Display the full transcript
# ---------------------------------------------------------------------------

# The API returns the transcript in two formats:
# 1. "transcripts" - An array of individual utterance objects with speaker labels
#    and timestamps. Useful for programmatic processing.
# 2. "concatenated_transcript" - The full transcript as a single string with
#    speaker labels. Easier to read.

concatenated = data.get("concatenated_transcript", "")

if concatenated:
    print("=" * 60)
    print("TRANSCRIPT")
    print("=" * 60)
    print()
    print(concatenated)
    print()
else:
    # If no concatenated transcript, try the structured transcripts array.
    transcripts = data.get("transcripts", [])
    if transcripts:
        print("=" * 60)
        print("TRANSCRIPT")
        print("=" * 60)
        print()
        for entry in transcripts:
            # Each transcript entry has a "user" field (either "agent" or "user")
            # and a "text" field with what was said.
            speaker = entry.get("user", "unknown").upper()
            text = entry.get("text", "")
            print("[{}] {}".format(speaker, text))
        print()
    else:
        print("No transcript available yet.")
        print("If the call just ended, wait a few seconds and try again.")
        print()

# ---------------------------------------------------------------------------
# Display the AI-generated summary
# ---------------------------------------------------------------------------

summary = data.get("summary", "")
if summary:
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()
    print(summary)
    print()

# ---------------------------------------------------------------------------
# Display extracted variables (if any)
# ---------------------------------------------------------------------------

# Variables can be extracted during the call based on your prompt instructions.
# For example, if the agent is supposed to collect a name and date, those
# values might appear here.

variables = data.get("variables", {})
if variables:
    print("=" * 60)
    print("EXTRACTED VARIABLES")
    print("=" * 60)
    print()
    for key, value in variables.items():
        print("  {}: {}".format(key, value))
    print()

# ---------------------------------------------------------------------------
# Display the raw JSON (for debugging)
# ---------------------------------------------------------------------------

# Uncomment the lines below to see the full raw API response.
# This is helpful for debugging or when you need to see every field.

# print("=" * 60)
# print("RAW API RESPONSE")
# print("=" * 60)
# print()
# print(json.dumps(data, indent=2))
# print()

print("=" * 60)
print("Done.")
