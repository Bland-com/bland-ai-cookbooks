"""
Bland AI - Create a Batch Campaign (Python)

This script reads a CSV file of patient records and submits them as a batch
campaign to the Bland AI API. Each row in the CSV becomes a personalized
outbound call. A shared "global" configuration provides the prompt template,
voice, and other defaults that apply to every call.

Use case: A dental office calling patients to remind them of upcoming
appointments. Each call is personalized with the patient's name, appointment
date and time, dentist name, and service type.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. (Optional) Edit sample_leads.csv with your own phone numbers for testing.
    4. Run: python create_batch.py

The script will:
    - Read the CSV file
    - Build a call_objects array with one entry per row
    - Attach a global configuration with the prompt template
    - Submit the batch to the Bland API
    - Print the batch_id for monitoring
"""

import csv
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

# Path to the CSV file containing patient records.
# Default is "sample_leads.csv" in the same directory as this script.
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "sample_leads.csv")

# (Optional) Webhook URL for receiving batch lifecycle status updates.
# If set, Bland will POST to this URL as the batch moves through each stage.
STATUS_WEBHOOK = os.getenv("STATUS_WEBHOOK", "")

# The Bland API base URL. All endpoints are under this path.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Read the CSV file
# ---------------------------------------------------------------------------

# Resolve the CSV path relative to the script's directory.
# This ensures the script works regardless of where it is called from.
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, CSV_FILE_PATH)

if not os.path.exists(csv_path):
    print("Error: CSV file not found at '{}'.".format(csv_path))
    print("Make sure the file exists or update CSV_FILE_PATH in your .env file.")
    sys.exit(1)

print("Reading CSV file: {}".format(csv_path))
print()

# Parse the CSV. Each row becomes one call in the batch.
# The column names are used as keys in the request_data for each call,
# making them available as {{column_name}} template variables in the prompt.
call_objects = []

with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)

    # Validate that the required "phone_number" column exists.
    if "phone_number" not in reader.fieldnames:
        print("Error: CSV file must have a 'phone_number' column.")
        print("Found columns: {}".format(", ".join(reader.fieldnames)))
        sys.exit(1)

    for row_number, row in enumerate(reader, start=2):
        # Extract the phone number. This is the only required field per call.
        phone_number = row.get("phone_number", "").strip()

        if not phone_number:
            print("Warning: Row {} has no phone number. Skipping.".format(row_number))
            continue

        # Build the call object for this row.
        # The phone_number is required. All other CSV columns go into
        # request_data so they can be referenced as {{variable}} in the prompt.
        call_entry = {
            # REQUIRED: The phone number to call for this specific contact.
            "phone_number": phone_number,

            # OPTIONAL: Per-call request_data populated from CSV columns.
            # Each key-value pair here becomes a template variable.
            # For example, if the CSV has a "patient_name" column with value
            # "Sarah Johnson", then {{patient_name}} in the prompt will be
            # replaced with "Sarah Johnson" for this call.
            "request_data": {
                key: value.strip()
                for key, value in row.items()
                if key != "phone_number" and value
            },
        }

        # OPTIONAL: You can add per-call overrides here. Any parameter from
        # the /v1/calls API can be set on individual calls to override the
        # global defaults. For example:
        #
        # call_entry["voice"] = "mason"          # Different voice for this call
        # call_entry["language"] = "babel-es"     # Spanish for this contact
        # call_entry["max_duration"] = 10         # Longer max duration
        # call_entry["start_time"] = "2026-03-15T09:00:00-05:00"  # Schedule it

        call_objects.append(call_entry)

print("Loaded {} contacts from CSV.".format(len(call_objects)))
print()

if len(call_objects) == 0:
    print("Error: No valid contacts found in the CSV file.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Define the global configuration
# ---------------------------------------------------------------------------

# The global config contains settings that apply to every call in the batch.
# Think of this as the "template" that all calls share. Individual calls can
# override any of these settings in their call_entry.
#
# IMPORTANT: The global config MUST include either "task" or "pathway_id".
#            It CANNOT include "phone_number" (that is per-call only).

global_config = {
    # REQUIRED (one of task or pathway_id): The prompt template for the agent.
    # Use {{variable_name}} syntax to reference CSV columns. These variables
    # are automatically populated from each row's request_data.
    "task": """You are a friendly, professional receptionist for Bright Smile Dental Clinic.
You are calling {{patient_name}} to remind them about their upcoming dental appointment.

Appointment details:
- Date: {{appointment_date}}
- Time: {{appointment_time}}
- Dentist: {{dentist_name}}
- Service: {{service_type}}

Your goals:
1. Greet the patient warmly by name.
2. Confirm their appointment details (date, time, dentist, and service).
3. Ask if they need to reschedule. If yes, let them know someone from the office
   will call them back to find a new time.
4. Remind them to arrive 10 minutes early and bring their insurance card.
5. Ask if they have any questions.
6. Thank them and end the call politely.

Important guidelines:
- Keep responses to one or two sentences at a time. Phone conversations should feel natural and concise.
- If the patient wants to cancel entirely, express understanding and let them know they can
  call back anytime to rebook.
- If the patient asks medical questions, let them know the dentist will be happy to discuss
  that during their visit.
- Be warm and reassuring, especially if the patient seems nervous about their procedure.
- If you reach voicemail, leave a brief, friendly reminder message with the appointment details.""",

    # OPTIONAL: The exact first sentence the agent says when the call connects.
    # Using template variables here personalizes the greeting immediately.
    "first_sentence": (
        "Hi, is this {{patient_name}}? "
        "This is Bright Smile Dental Clinic calling with a quick reminder about your upcoming appointment."
    ),

    # OPTIONAL: The voice the agent uses for all calls in the batch.
    # Available voices: "mason", "maya", "ryan", "tina", "josh",
    #                   "florian", "derek", "june", "nat", "paige"
    "voice": "maya",

    # OPTIONAL: Which model to use for generating responses.
    # "base"  - Full-featured model with all capabilities.
    # "turbo" - Lowest latency, but may lack some features.
    "model": "base",

    # OPTIONAL: Maximum call length in minutes. For short reminder calls,
    # 5 minutes is usually plenty. This prevents runaway calls that could
    # consume excessive credits.
    "max_duration": 5,

    # OPTIONAL: Whether to record calls. Useful for quality assurance.
    # When True, recording_url will be available in call details after completion.
    "record": True,

    # OPTIONAL: Controls randomness in responses.
    # 0.0 = deterministic, 1.0 = most creative.
    # 0.7 is a good default for natural conversation.
    "temperature": 0.7,

    # OPTIONAL: What to do when the call goes to voicemail.
    # "action" options: "hangup", "leave_message", "ignore"
    # For appointment reminders, leaving a voicemail is usually the best choice.
    "voicemail": {
        "action": "leave_message",
        "message": (
            "Hi {{patient_name}}, this is Bright Smile Dental Clinic. "
            "We are calling to remind you about your {{service_type}} appointment "
            "on {{appointment_date}} at {{appointment_time}} with {{dentist_name}}. "
            "Please arrive 10 minutes early and bring your insurance card. "
            "If you need to reschedule, please call us back. Thank you!"
        ),
    },

    # OPTIONAL: If True, the agent waits for the human to speak first.
    # For outbound reminder calls, you want the agent to speak first.
    "wait_for_greeting": False,

    # OPTIONAL: Ambient background audio for realism.
    # Options: null, "office", "cafe", "restaurant", "none"
    "background_track": "office",
}

# ---------------------------------------------------------------------------
# Build the batch payload
# ---------------------------------------------------------------------------

# The batch payload combines the call_objects array with the global config.
# The global config provides defaults that apply to every call.
# Each call_entry in call_objects can override any global setting.

batch_payload = {
    # REQUIRED: Array of individual call entries. Each entry must have at least
    # a "phone_number". All other fields are optional and override the global
    # config for that specific call.
    "call_objects": call_objects,

    # REQUIRED: Default settings applied to all calls unless overridden.
    # Must include "task" or "pathway_id". Cannot include "phone_number".
    "global": global_config,
}

# Add the status webhook if one was configured.
# The webhook receives POST requests as the batch moves through its lifecycle:
# validating -> dispatching -> in_progress -> completed (or failed)
if STATUS_WEBHOOK:
    batch_payload["status_webhook"] = STATUS_WEBHOOK

# ---------------------------------------------------------------------------
# Submit the batch
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print("Submitting batch of {} calls to Bland API...".format(len(call_objects)))
print()

try:
    # Make the POST request to the Create Batch endpoint.
    response = requests.post(
        "{}/batches".format(BASE_URL),
        json=batch_payload,
        headers=headers,
        timeout=60,  # Larger batches may take a moment to process
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

# ---------------------------------------------------------------------------
# Handle the response
# ---------------------------------------------------------------------------

# Parse the JSON response.
data = response.json()

# The successful response has this structure:
# { "data": { "batch_id": "uuid" }, "errors": null }
if data.get("data") and data["data"].get("batch_id"):
    batch_id = data["data"]["batch_id"]
    print("Batch successfully created!")
    print("Batch ID: {}".format(batch_id))
    print()
    print("Total calls in batch: {}".format(len(call_objects)))
    print()
    print("To monitor this batch, run:")
    print("  python monitor_batch.py {}".format(batch_id))
    print()
    print("To stop this batch, run:")
    print("  python stop_batch.py {}".format(batch_id))

    if STATUS_WEBHOOK:
        print()
        print("Status webhook configured: {}".format(STATUS_WEBHOOK))
        print("You will receive POST requests as the batch progresses.")
elif data.get("errors"):
    # The API returned validation errors.
    print("Batch creation failed with errors:")
    print(data["errors"])
    sys.exit(1)
else:
    # Unexpected response format.
    print("Unexpected response from API:")
    print(data)
    sys.exit(1)
