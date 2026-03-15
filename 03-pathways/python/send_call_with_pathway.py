"""
send_call_with_pathway.py

Sends a phone call using an existing Bland AI pathway. Instead of providing
a task prompt, you reference a pathway_id and the agent follows the
structured conversation flow defined in the pathway.

You can also pass request_data to pre-populate variables that the pathway
can use from the very start of the call.

Usage:
  1. Copy .env.example to .env and fill in your API key, pathway ID, and phone number
  2. pip install requests python-dotenv
  3. python send_call_with_pathway.py

Prerequisites:
  - Run create_pathway.py first to get a pathway_id, or use one from the dashboard
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory
load_dotenv()

# Your Bland AI API key
BLAND_API_KEY = os.getenv("BLAND_API_KEY")

# The pathway ID to use for this call.
# You get this from create_pathway.py or from the Bland dashboard.
PATHWAY_ID = os.getenv("PATHWAY_ID")

# The phone number to call. Must be in E.164 format (e.g., +12223334444).
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# Base URL and headers for the Bland API
BASE_URL = "https://api.bland.ai/v1"
HEADERS = {
    "Authorization": BLAND_API_KEY,
    "Content-Type": "application/json",
}


def send_call_with_pathway():
    """
    Send a phone call that uses a pathway instead of a simple task prompt.

    POST https://api.bland.ai/v1/calls
    Body: {
        "phone_number": "+1...",
        "pathway_id": "uuid",
        "request_data": { ... }
    }

    Key differences from a regular task-based call:
      - Use "pathway_id" instead of "task"
      - The agent follows the node/edge structure of the pathway
      - You can pass "request_data" to inject variables into the pathway
        before the call starts (useful for personalization)

    Returns the call_id which you can use to check call status and
    retrieve the transcript later.
    """
    url = f"{BASE_URL}/calls"

    payload = {
        # The phone number to dial. Must include country code.
        "phone_number": PHONE_NUMBER,

        # The pathway_id tells Bland to use a structured pathway
        # instead of a freeform task prompt. The agent will start
        # at the node marked isStart: true and follow edges based
        # on the conversation.
        "pathway_id": PATHWAY_ID,

        # request_data lets you pass variables into the pathway before
        # the call even starts. These become available as {{variable_name}}
        # in any node prompt.
        #
        # This is useful for personalization. For example, if you know the
        # caller's name from your CRM, you can pass it here and reference
        # it in your greeting node with {{customer_name}}.
        "request_data": {
            "restaurant_name": "Mario's Italian Kitchen",
            "customer_name": "Valued Guest",
        },

        # voice_id: Optionally specify which voice the agent should use.
        # Browse available voices at https://app.bland.ai/voices
        # Uncomment and set a voice ID if you want a specific voice:
        # "voice_id": "your-voice-id-here",

        # max_duration: Maximum call length in minutes. The call will
        # automatically end after this many minutes. Default is 30.
        # Set lower for testing to avoid accidental long calls.
        "max_duration": 5,

        # record: Whether to record the call audio. Defaults to true.
        # The recording URL will be available in the call details after
        # the call ends.
        "record": True,
    }

    print(f"Sending call to {PHONE_NUMBER} using pathway {PATHWAY_ID}...")
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()

    data = response.json()
    call_id = data.get("call_id")

    print(f"\nCall dispatched successfully!")
    print(f"Call ID: {call_id}")
    print(f"\nFull response:\n{json.dumps(data, indent=2)}")
    print(f"\nThe call is now in progress. You can check its status with:")
    print(f"  GET {BASE_URL}/calls/{call_id}")

    return data


def main():
    """
    Validate configuration and send the call.
    """
    # Check that all required environment variables are set
    missing = []
    if not BLAND_API_KEY:
        missing.append("BLAND_API_KEY")
    if not PATHWAY_ID:
        missing.append("PATHWAY_ID")
    if not PHONE_NUMBER:
        missing.append("PHONE_NUMBER")

    if missing:
        print("Error: Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nCopy .env.example to .env and fill in the values.")
        print("Run create_pathway.py first to get a PATHWAY_ID.")
        return

    send_call_with_pathway()


if __name__ == "__main__":
    main()
