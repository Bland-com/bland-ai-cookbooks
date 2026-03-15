"""
Bland AI - Send a Call with a Persona (Python)

This script sends an outbound phone call using a persona_id, which means
the persona's voice, prompt, model, and behavior settings serve as the
baseline configuration for the call. You can also override specific
persona settings on a per-call basis by including additional parameters.

Usage:
    1. Copy .env.example to .env and fill in your API key, phone number,
       and persona_id (from running create_persona.py).
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python send_call_with_persona.py

The script will:
    - Send a call using the persona's configuration as the baseline
    - Demonstrate how to override specific persona settings
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
# This keeps your API key out of source control.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
API_KEY = os.getenv("BLAND_API_KEY")

# The phone number to call, in E.164 format (e.g., +15551234567).
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# The persona ID to use for this call. This was returned when you created
# the persona using create_persona.py. All of the persona's settings
# (voice, prompt, model, interruption threshold, etc.) are applied
# automatically as the baseline for the call.
PERSONA_ID = os.getenv("PERSONA_ID")

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

if not PERSONA_ID:
    print("Error: PERSONA_ID is not set.")
    print("Run create_persona.py first to create a persona, then add the")
    print("persona_id to your .env file.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Build the request payload
# ---------------------------------------------------------------------------

# When using a persona_id, the persona's configuration serves as the
# baseline for the call. You only need to provide the phone_number and
# persona_id. The persona's voice, prompt, model, and all other settings
# are applied automatically.
#
# However, you can override any persona setting by including additional
# parameters in the request body. Parameters you include here take
# precedence over the persona defaults.

payload = {
    # REQUIRED: The phone number to call in E.164 format.
    "phone_number": PHONE_NUMBER,

    # REQUIRED: The persona ID. This tells the API to use the persona's
    # configuration (voice, prompt, model, etc.) as the baseline for
    # this call. You created this persona using create_persona.py.
    "persona_id": PERSONA_ID,

    # -----------------------------------------------------------------------
    # OPTIONAL OVERRIDES
    # -----------------------------------------------------------------------
    # Any parameters you include below will override the persona's defaults
    # for this specific call. The persona itself is not modified.
    # Uncomment any of these to override the persona settings.

    # Override the first sentence for this specific call.
    # This replaces the persona's default greeting with a more targeted one.
    # Useful when you know the reason for the call ahead of time.
    # "first_sentence": "Hi! I am calling about your recent support ticket.",

    # Override the maximum call duration for this specific call.
    # The persona may not have a max_duration set, or you may want a
    # different limit for this particular call.
    "max_duration": 10,

    # Enable recording for this specific call. When True, a recording_url
    # will be available in the call details after the call completes.
    # This is a per-call setting that does not affect the persona.
    "record": True,

    # Pass dynamic data that can be referenced in the persona's prompt
    # using {{variable_name}} syntax. This is a powerful way to personalize
    # calls without modifying the persona itself.
    "request_data": {
        "customer_name": "Alex Johnson",
        "account_email": "alex.johnson@example.com",
        "ticket_number": "TC-2024-4521",
    },

    # Override voicemail behavior for this specific call.
    # This controls what happens if the call goes to voicemail.
    "voicemail": {
        # "hangup" ends the call immediately when voicemail is detected.
        # "leave_message" leaves the specified message.
        # "ignore" continues as if speaking to a person.
        "action": "leave_message",
        "message": (
            "Hi, this is Sarah from TechCorp Customer Success. "
            "I was calling to check in on your recent support request. "
            "Please call us back at your convenience, or reply to the "
            "email we sent. Thank you!"
        ),
    },

    # Add a pronunciation guide for words the agent might mispronounce.
    # This is especially useful for brand names, product names, acronyms,
    # and technical terms.
    "pronunciation_guide": [
        {
            # The word to match in the agent's output text.
            "word": "TechCorp",
            # How the agent should say it. Write it phonetically.
            "pronunciation": "Tek-corp",
            # If True, only matches the exact casing ("TechCorp" but not
            # "techcorp"). If False, matches regardless of case.
            "case_sensitive": True,
            # If True, the word is spelled out letter by letter.
            # If False, it is spoken as a single word.
            "spaced": False,
        },
        {
            "word": "SSO",
            "pronunciation": "S-S-O",
            "case_sensitive": False,
            # Spaced is True here because we want each letter pronounced
            # individually: "S, S, O" rather than "sso".
            "spaced": True,
        },
    ],
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

print("Sending call with persona: {}".format(PERSONA_ID))
print("Calling: {}".format(PHONE_NUMBER))
print()

try:
    # Make the POST request to the Send Call endpoint.
    # The persona_id tells the API to load the persona's configuration
    # as the baseline. Any additional parameters in the payload override
    # the persona's defaults for this call only.
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

# Parse the JSON response.
data = response.json()

# ---------------------------------------------------------------------------
# Display the results
# ---------------------------------------------------------------------------

# Check if the call was successfully queued.
if data.get("status") == "success":
    call_id = data["call_id"]
    print("Call successfully queued!")
    print()
    print("  Call ID:    {}".format(call_id))
    print("  Persona:   {}".format(PERSONA_ID))
    print("  Phone:     {}".format(PHONE_NUMBER))
    print("  Recording: Enabled")
    print()
    print("Your phone should ring shortly. Answer it to talk with the AI agent.")
    print("The agent will use the persona's voice, prompt, and behavior settings.")
    print()
    print("After the call, check the Bland dashboard to review:")
    print("  - Full transcript")
    print("  - Post-call analysis (based on the persona's analysis_schema)")
    print("  - Recording (since record=True)")
    print()

    # -----------------------------------------------------------------------
    # Demonstrate how to fetch the persona details for verification
    # -----------------------------------------------------------------------

    print("Verifying persona configuration...")
    print()

    try:
        # Fetch the persona details to confirm the configuration.
        # This GET request returns the full persona object, including
        # all settings that will be used as the baseline for the call.
        persona_response = requests.get(
            "{}/personas/{}".format(BASE_URL, PERSONA_ID),
            headers={"Authorization": API_KEY},
            timeout=15,
        )
        persona_response.raise_for_status()
        persona_data = persona_response.json()

        # Display key persona settings so the user can verify them.
        print("Persona details:")
        print("  Name:        {}".format(persona_data.get("name", "Unknown")))
        print("  Voice:       {}".format(persona_data.get("voice", "Unknown")))
        print("  Model:       {}".format(persona_data.get("model", "Unknown")))
        print("  Language:    {}".format(persona_data.get("language", "Unknown")))
        print()

    except requests.exceptions.RequestException:
        # If we cannot fetch the persona details, it is not critical.
        # The call has already been queued successfully.
        print("Could not fetch persona details (non-critical). The call")
        print("has been queued and will use the persona's configuration.")
        print()

else:
    # If the status is not "success", print the full response for debugging.
    print("Unexpected response from API:")
    print(data)
    sys.exit(1)

# ---------------------------------------------------------------------------
# What happens during the call
# ---------------------------------------------------------------------------

print("What to expect:")
print("  1. The agent will greet you using the persona's first_sentence.")
print("  2. The agent speaks with the persona's selected voice.")
print("  3. The agent follows the persona's prompt and personality rules.")
print("  4. Background audio (if configured) plays during the call.")
print("  5. After the call, the analysis_schema fields are populated")
print("     automatically based on the conversation.")
