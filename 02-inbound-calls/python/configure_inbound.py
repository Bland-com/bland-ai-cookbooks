"""
configure_inbound.py
====================
Configure an AI agent to answer calls on your Bland AI inbound number.

This script sends a POST request to set up the agent's prompt, voice,
greeting, transfer rules, and advanced settings. Once configured, anyone
who calls your number will be greeted by your AI agent.

The example below sets up a business front desk receptionist that:
  - Greets callers warmly
  - Asks how it can help
  - Routes calls to Sales, Support, or Billing
  - Collects caller information
  - Handles common questions

Usage:
    1. Copy .env.example to .env and add your API key.
    2. Set INBOUND_NUMBER below to the number you purchased.
    3. Customize the prompt and settings to fit your use case.
    4. Run: python configure_inbound.py

Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from the .env file in this directory.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Your Bland AI API key, loaded from the .env file.
API_KEY = os.getenv("BLAND_API_KEY")

# The inbound phone number you purchased, with country code and "+" prefix.
# Replace this with the number you got from purchase_number.py.
# Example: "+14155551234"
INBOUND_NUMBER = "+1XXXXXXXXXX"  # <-- PASTE YOUR NUMBER HERE

# The Bland AI API endpoint for configuring an inbound number.
# The phone number is included in the URL path.
CONFIGURE_URL = f"https://api.bland.ai/v1/inbound/{INBOUND_NUMBER}"

# ---------------------------------------------------------------------------
# Agent Configuration
#
# This is where you define everything about how the AI agent behaves when
# it answers a call. The prompt is the most important part. Think of it as
# the agent's instruction manual.
# ---------------------------------------------------------------------------

AGENT_CONFIG = {

    # -----------------------------------------------------------------------
    # prompt (string, required)
    #
    # The core instructions for your AI agent. This tells the agent who it
    # is, how to behave, and what to do in different situations. Be specific
    # and thorough. The more detail you provide, the better the agent will
    # perform.
    #
    # Tips for writing good prompts:
    #   - Give the agent a name and role
    #   - List the departments or people it can transfer to
    #   - Describe how to handle common questions
    #   - Specify what info to collect from callers
    #   - Set a tone (professional, friendly, formal, casual)
    # -----------------------------------------------------------------------
    "prompt": """You are Alex, the front desk receptionist at Meridian Solutions.
Your job is to answer incoming calls professionally and help callers get to
the right person or department.

## Your Responsibilities
- Greet every caller warmly and ask how you can help.
- Identify what the caller needs and route them to the correct department.
- Answer basic questions about the company (hours, location, services).
- Collect the caller's name and reason for calling before transferring.

## Company Information
- Company: Meridian Solutions
- Hours: Monday to Friday, 9 AM to 6 PM Eastern Time
- Location: 500 Innovation Drive, Suite 200, Austin, TX 78701
- Services: Business consulting, software development, and IT support

## Available Departments
- Sales: For new business inquiries, pricing, and demos
- Support: For existing customers needing technical help
- Billing: For invoices, payments, and account questions

## Transfer Rules
- Always ask the caller's name before transferring.
- Let the caller know which department you are transferring them to.
- If the caller is unsure which department they need, ask a few clarifying
  questions to figure it out.

## Tone
Be professional but warm. Use the caller's name once you know it. Keep
responses concise and helpful.""",

    # -----------------------------------------------------------------------
    # voice (string)
    #
    # The voice the agent uses when speaking. Bland AI offers several built-in
    # voices. Popular options include:
    #   "mason"  - Male, professional, clear
    #   "josh"   - Male, friendly, conversational
    #   "emma"   - Female, warm, professional
    #   "tina"   - Female, upbeat, energetic
    #
    # You can also use custom cloned voice IDs if you have created one.
    # -----------------------------------------------------------------------
    "voice": "mason",

    # -----------------------------------------------------------------------
    # first_sentence (string)
    #
    # The very first thing callers hear when the agent picks up the phone.
    # Make it sound natural, like a real receptionist answering. This is
    # spoken immediately, before the agent reads the prompt, so keep it
    # short and welcoming.
    # -----------------------------------------------------------------------
    "first_sentence": "Thank you for calling Meridian Solutions, this is Alex. How can I help you today?",

    # -----------------------------------------------------------------------
    # model (string)
    #
    # Which AI model to use for generating responses:
    #   "base"  - More cost-effective, good for straightforward conversations
    #   "turbo" - Faster responses, better at complex reasoning
    #
    # Start with "base" and switch to "turbo" if you need snappier replies.
    # -----------------------------------------------------------------------
    "model": "base",

    # -----------------------------------------------------------------------
    # language (string)
    #
    # The language the agent speaks. Use standard language codes:
    #   "en" = English
    #   "es" = Spanish
    #   "fr" = French
    #   "de" = German
    #   ... and many more
    # -----------------------------------------------------------------------
    "language": "en",

    # -----------------------------------------------------------------------
    # max_duration (integer)
    #
    # Maximum call length in minutes. The agent will politely end the call
    # when this limit is reached. Set this to avoid unexpectedly long (and
    # expensive) calls.
    #
    # Recommended values:
    #   5  - Quick routing or FAQ calls
    #   15 - Standard customer interactions
    #   30 - Detailed consultations
    # -----------------------------------------------------------------------
    "max_duration": 15,

    # -----------------------------------------------------------------------
    # record (boolean)
    #
    # Whether to record the call audio. Recorded calls can be reviewed
    # later for quality assurance or training. Set to True if you need
    # call recordings, False if you only need the transcript.
    # -----------------------------------------------------------------------
    "record": True,

    # -----------------------------------------------------------------------
    # transfer_list (object)
    #
    # A dictionary mapping department names to phone numbers. When the agent
    # decides to transfer a call, it matches the department name mentioned
    # in the conversation to one of these entries.
    #
    # Make sure the department names here match what you described in the
    # prompt above so the agent knows they exist.
    #
    # Replace these placeholder numbers with real phone numbers.
    # -----------------------------------------------------------------------
    "transfer_list": {
        "Sales": "+14155559999",     # Replace with your Sales team number
        "Support": "+14155558888",   # Replace with your Support team number
        "Billing": "+14155557777",   # Replace with your Billing team number
    },

    # -----------------------------------------------------------------------
    # webhook (string)
    #
    # A URL that Bland AI will send a POST request to after each call ends.
    # The webhook payload includes the full transcript, call duration,
    # metadata, and any data extracted via analysis_schema.
    #
    # Useful for pushing call data to your CRM, logging system, or analytics
    # pipeline. Set to None or remove this key if you do not need webhooks.
    #
    # Example: "https://your-server.com/api/bland-webhook"
    # -----------------------------------------------------------------------
    "webhook": None,

    # -----------------------------------------------------------------------
    # background_track (string)
    #
    # Ambient audio played behind the agent's voice to make the call feel
    # more realistic. Options include:
    #   "office"           - Subtle office ambiance
    #   "convention_hall"  - Busy conference background
    #   None               - No background audio (default)
    # -----------------------------------------------------------------------
    "background_track": "office",

    # -----------------------------------------------------------------------
    # interruption_threshold (number)
    #
    # Controls how sensitive the agent is to being interrupted by the caller.
    # Range: 50 to 200.
    #
    #   50  - Very sensitive; the agent pauses as soon as the caller speaks
    #   100 - Balanced (good default)
    #   200 - Very patient; the agent finishes its thought even if the caller
    #         starts talking
    #
    # Lower values feel more conversational. Higher values are better when
    # the agent needs to deliver important information without being cut off.
    # -----------------------------------------------------------------------
    "interruption_threshold": 100,

    # -----------------------------------------------------------------------
    # noise_cancellation (boolean)
    #
    # Filters out background noise from the caller's environment. Helps
    # improve transcription accuracy when callers are in noisy places
    # (cars, restaurants, outdoors).
    # -----------------------------------------------------------------------
    "noise_cancellation": True,

    # -----------------------------------------------------------------------
    # keywords (string[])
    #
    # Words or phrases to boost in the speech-to-text transcription model.
    # Add brand names, product names, technical terms, or any uncommon words
    # that callers might say. This helps the transcriber recognize them
    # accurately instead of guessing a more common word.
    # -----------------------------------------------------------------------
    "keywords": ["Meridian", "Meridian Solutions"],

    # -----------------------------------------------------------------------
    # analysis_schema (object)
    #
    # Defines what structured data to extract from the call after it ends.
    # Each key is a field name and the value is a description telling the
    # AI what to look for. The extracted data is included in the webhook
    # payload and available via the API.
    #
    # This is incredibly useful for automatically logging caller intent,
    # contact info, and outcomes without manual review.
    # -----------------------------------------------------------------------
    "analysis_schema": {
        "caller_name": "The full name of the caller, if they provided it.",
        "reason_for_calling": "A brief summary of why the caller called.",
        "department_transferred_to": "Which department the caller was transferred to, if any.",
        "caller_sentiment": "The overall sentiment of the caller: positive, neutral, or negative.",
        "follow_up_needed": "Whether a follow-up action is needed. True or false.",
    },

    # -----------------------------------------------------------------------
    # fallback_number (string)
    #
    # A phone number to redirect all calls to if you need to take the AI
    # agent offline temporarily (for example, during prompt updates or
    # maintenance). Callers will be forwarded to this number instead of
    # reaching the agent.
    #
    # Set to None or remove this key if you do not need a fallback.
    # -----------------------------------------------------------------------
    "fallback_number": None,
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def configure_inbound():
    """
    Send the agent configuration to Bland AI for the specified inbound number.

    Returns the API response as a dictionary.
    """

    # Verify the API key is set.
    if not API_KEY:
        print("Error: BLAND_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return None

    # Verify the user has set their inbound number.
    if INBOUND_NUMBER == "+1XXXXXXXXXX":
        print("Error: INBOUND_NUMBER has not been set.")
        print("Open this file and replace '+1XXXXXXXXXX' with the phone")
        print("number you purchased using purchase_number.py.")
        return None

    # Build request headers. Bland AI uses the raw key (no "Bearer" prefix).
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }

    # Remove any keys with None values from the config so we only send
    # the parameters we actually want to set.
    payload = {k: v for k, v in AGENT_CONFIG.items() if v is not None}

    print(f"Configuring inbound agent for {INBOUND_NUMBER}...")
    print(f"Request URL: {CONFIGURE_URL}")
    print(f"Voice: {payload.get('voice')}")
    print(f"Model: {payload.get('model')}")
    print(f"Max duration: {payload.get('max_duration')} minutes")
    print(f"Transfer departments: {list(payload.get('transfer_list', {}).keys())}")
    print()

    try:
        # Send the POST request with the full agent configuration.
        response = requests.post(CONFIGURE_URL, json=payload, headers=headers)

        # Parse the response.
        data = response.json()

        if response.status_code == 200:
            print("Success! Your inbound agent is now configured.")
            print(json.dumps(data, indent=2))
            print()
            print(f"Your agent is live. Call {INBOUND_NUMBER} to test it!")
        else:
            print(f"Error: Received status code {response.status_code}")
            print(json.dumps(data, indent=2))

        return data

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


if __name__ == "__main__":
    configure_inbound()
