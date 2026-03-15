"""
Bland AI - Create an AI-Powered SMS Conversation (Python)

This script creates an autonomous AI SMS conversation using the Bland AI API.
Once created, the AI agent will send the initial message and then handle all
follow-up replies automatically, following the prompt you define.

Use case: A dental office sends appointment follow-up texts to patients.
The AI agent confirms the appointment, answers questions about preparation,
and handles rescheduling requests.

Usage:
    1. Copy .env.example to .env and fill in your API key and phone numbers.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python create_conversation.py

The script will:
    - Create a new AI-powered SMS conversation
    - Print the conversation ID for tracking
    - The AI agent will then manage the conversation autonomously

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
API_KEY = os.getenv("BLAND_API_KEY")

# The phone number to send SMS from. This must be a Bland phone number
# that has been configured for SMS in your Bland dashboard.
FROM_NUMBER = os.getenv("FROM_NUMBER")

# The recipient's phone number in E.164 format (e.g., +15551234567).
# This is the person who will receive the AI-driven text conversation.
TO_NUMBER = os.getenv("TO_NUMBER")

# The Bland API base URL. All SMS endpoints are under /v1/sms.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

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
# Define the AI agent prompt
# ---------------------------------------------------------------------------

# The "prompt" tells the AI agent how to behave throughout the SMS conversation.
# This is similar to the "task" parameter for voice calls, but optimized for
# text messaging. The agent will follow these instructions for every message
# it sends and every reply it processes.
#
# Tips for writing SMS prompts:
#   - Keep responses concise. Text messages should be short and scannable.
#   - Avoid filler phrases like "uh-huh" or "got it" that feel unnatural in text.
#   - Be specific about what information to collect and what actions to take.
#   - Define a clear end state so the agent knows when the conversation is done.
#   - Consider that replies may be delayed by minutes, hours, or even days.

AGENT_PROMPT = """You are a friendly appointment follow-up assistant for Sunrise Dental.
Your name is Sam. You are texting a patient to confirm their upcoming dental appointment.

Appointment details:
- Patient name: the person you are texting
- Appointment date: Tomorrow at 10:00 AM
- Location: Sunrise Dental, 456 Oak Avenue, Suite 200
- Doctor: Dr. Martinez
- Type: Routine cleaning and checkup

Your goals:
1. Confirm the appointment. Ask the patient to reply "yes" to confirm or let you know if they need to reschedule.
2. If they confirm, remind them of the preparation instructions (listed below).
3. If they want to reschedule, ask for their preferred date and time, then let them know someone from the office will call to finalize.
4. Answer any questions they have about the appointment.

Preparation instructions to share when the patient confirms:
- Please arrive 10 minutes early to complete any paperwork.
- Brush and floss before your visit.
- Bring your insurance card and a photo ID.
- If you are taking any new medications, let us know when you arrive.

Important guidelines:
- Keep your messages short and friendly. One to three sentences per message is ideal for texting.
- Use a warm, professional tone. You represent a dental office, not a chatbot.
- Do not use medical jargon. Keep language simple and clear.
- If the patient has a question you cannot answer (like specific treatment costs or insurance coverage), let them know the office will follow up with details.
- Once the appointment is confirmed and instructions are shared, thank the patient and end the conversation.
- If the patient asks to cancel entirely, express understanding and let them know the office will reach out to reschedule when they are ready.

Example opening message: "Hi! This is Sam from Sunrise Dental. Just a friendly reminder that you have an appointment tomorrow at 10:00 AM with Dr. Martinez for a routine cleaning. Can you confirm you will be there?"
"""

# ---------------------------------------------------------------------------
# Build the request payload
# ---------------------------------------------------------------------------

# The payload contains all the parameters for the Create SMS Conversation endpoint.
# Required fields: phone_number, from, prompt (or pathway_id).
# The AI agent will use these instructions to manage the entire conversation.

payload = {
    # REQUIRED: The recipient's phone number in E.164 format.
    # The AI agent will send the initial message to this number and
    # handle all subsequent replies.
    "phone_number": TO_NUMBER,

    # REQUIRED: Your Bland phone number that will appear as the sender.
    # This number must be SMS-configured in your Bland dashboard.
    "from": FROM_NUMBER,

    # REQUIRED (unless using pathway_id): The instructions for the AI agent.
    # This defines the agent's personality, goals, and behavior for the
    # entire conversation. The agent will reference this prompt for every
    # message it sends and every reply it processes.
    "prompt": AGENT_PROMPT,

    # OPTIONAL: Use a pathway instead of a prompt for conversation logic.
    # Pathways let you build visual conversation flows in the Bland dashboard.
    # If you set pathway_id, the agent follows the pathway instead of the prompt.
    # Note: When using a pathway, backchanneling phrases are automatically
    # stripped from responses to keep text messages clean and natural.
    # "pathway_id": "your-pathway-id-here",

    # OPTIONAL: Pin the conversation to a specific version of the pathway.
    # This is useful if you have published multiple versions and want to
    # ensure this conversation uses a particular one.
    # "pathway_version": 1,

    # OPTIONAL: Start the conversation at a specific node in the pathway.
    # By default, the conversation starts at the pathway's entry node.
    # Use this to skip ahead to a particular step in the flow.
    # "node_id": "specific-node-id-here",
}

# ---------------------------------------------------------------------------
# Create the SMS conversation
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print("Creating AI-powered SMS conversation...")
print("From: {}".format(FROM_NUMBER))
print("To: {}".format(TO_NUMBER))
print()

try:
    # Make the POST request to the Create SMS Conversation endpoint.
    # This creates the conversation and sends the first message immediately.
    # The AI agent will then handle all follow-up replies autonomously.
    response = requests.post(
        "{}/sms/create".format(BASE_URL),
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

    if response.status_code == 401:
        print()
        print("This usually means your API key is invalid or missing.")
    elif response.status_code == 400:
        print()
        print("This usually means one of the parameters is invalid.")
        print("Check that your phone numbers are in E.164 format")
        print("and that your FROM_NUMBER is SMS-configured.")
    elif response.status_code == 403:
        print()
        print("SMS may not be enabled on your plan.")
        print("SMS is an Enterprise feature. Contact Bland support to enable it.")

    sys.exit(1)

# ---------------------------------------------------------------------------
# Handle the response
# ---------------------------------------------------------------------------

# Parse the JSON response from the API.
data = response.json()

print("SMS conversation created successfully!")
print()

# Print all fields returned in the response.
print("Response from API:")
for key, value in data.items():
    print("  {}: {}".format(key, value))

print()
print("The AI agent has sent the initial message to {}.".format(TO_NUMBER))
print("The agent will now handle all replies autonomously,")
print("following the prompt instructions you provided.")
print()
print("To view this conversation later, use:")
print("  python list_conversations.py")
print()
print("Or check the SMS section in the Bland dashboard at https://app.bland.ai")
