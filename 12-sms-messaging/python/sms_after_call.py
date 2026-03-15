"""
Bland AI - Send an SMS Follow-Up After a Phone Call (Python)

This script demonstrates a common workflow: after an AI phone call completes,
send an SMS follow-up to the customer with a summary, next steps, or a
confirmation of what was discussed.

The workflow:
  1. Send a phone call with an analysis_schema to extract key details.
  2. Wait for the call to complete.
  3. Read the extracted data (customer name, email, follow-up preferences).
  4. Send a personalized SMS to the customer based on the call outcome.

This is one of the most powerful patterns in Bland: combining voice calls
with automated SMS follow-ups so no lead or customer falls through the cracks.

Usage:
    1. Copy .env.example to .env and fill in your API key and phone numbers.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python sms_after_call.py

Note: SMS messaging is an Enterprise feature. Your Bland phone number
must be configured for SMS, and US numbers require A2P 10DLC registration.
"""

import os
import sys
import json
import time

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
API_KEY = os.getenv("BLAND_API_KEY")

# The phone number to call AND text. In this workflow, we call the customer
# first, then send them a text after the call with a summary.
TO_NUMBER = os.getenv("TO_NUMBER")

# Your Bland phone number (must be configured for both voice and SMS).
FROM_NUMBER = os.getenv("FROM_NUMBER")

# The Bland API base URL.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

if not TO_NUMBER:
    print("Error: TO_NUMBER is not set.")
    print("Add the recipient's phone number in E.164 format to .env.")
    sys.exit(1)

if not FROM_NUMBER:
    print("Error: FROM_NUMBER is not set.")
    print("Add your Bland phone number (voice + SMS configured) to .env.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# HTTP headers
# ---------------------------------------------------------------------------

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# Step 1: Send the phone call
# ---------------------------------------------------------------------------

print("=" * 60)
print("VOICE CALL + SMS FOLLOW-UP WORKFLOW")
print("=" * 60)
print()

# The agent collects information during the call. The analysis_schema
# tells Bland what to extract from the transcript afterward.
call_payload = {
    "phone_number": TO_NUMBER,
    "from": FROM_NUMBER,
    "task": """You are Jamie from Greenfield Insurance, calling to discuss
a customer's auto insurance renewal. Their policy is up for renewal next month.

Your goals:
1. Greet the customer and let them know their policy is renewing soon.
2. Ask if they want to keep the same coverage or if anything has changed
   (new car, new driver, address change).
3. Mention that you can offer a multi-policy discount if they bundle home
   and auto insurance.
4. Ask if they have any questions about their coverage.
5. Let them know you will send a follow-up text with a summary and a link
   to review their policy online.
6. Thank them and wrap up.

Keep the conversation professional and helpful. If they want to make changes,
note what they want changed and let them know you will include it in the
follow-up text.""",
    "analysis_schema": {
        "customer_name": "The customer's name.",
        "wants_changes": (
            "Does the customer want to make any changes to their policy? "
            "true or false."
        ),
        "requested_changes": (
            "If they want changes, describe what they requested. "
            "Null if no changes."
        ),
        "interested_in_bundle": (
            "Is the customer interested in a multi-policy bundle discount? "
            "true, false, or maybe."
        ),
        "has_questions": (
            "Did the customer have any unresolved questions? true or false."
        ),
        "question_summary": (
            "Brief summary of any questions the customer asked. "
            "Null if no questions."
        ),
    },
    "record": True,
    "max_duration": 5,
}

print("Step 1: Sending phone call to {}...".format(TO_NUMBER))
print()

try:
    call_response = requests.post(
        "{}/calls".format(BASE_URL),
        json=call_payload,
        headers=headers,
        timeout=30,
    )
    call_response.raise_for_status()
except requests.exceptions.RequestException as e:
    print("Error sending call: {}".format(e))
    if hasattr(e, "response") and e.response is not None:
        print("Response: {}".format(e.response.text))
    sys.exit(1)

call_data = call_response.json()
call_id = call_data.get("call_id")

if not call_id:
    print("Error: No call_id returned.")
    print(json.dumps(call_data, indent=2))
    sys.exit(1)

print("Call queued! Call ID: {}".format(call_id))
print()

# ---------------------------------------------------------------------------
# Step 2: Wait for the call to complete
# ---------------------------------------------------------------------------

print("Step 2: Waiting for the call to complete...")
print("(Answer your phone when it rings!)")
print()

for attempt in range(60):
    try:
        poll = requests.get(
            "{}/calls/{}".format(BASE_URL, call_id),
            headers=headers,
            timeout=15,
        )
        poll.raise_for_status()
        poll_data = poll.json()

        if poll_data.get("completed") or poll_data.get("status") == "completed":
            print("Call completed!")
            print()
            break

        elapsed = (attempt + 1) * 5
        print("  Waiting... ({}s)".format(elapsed))

    except requests.exceptions.RequestException:
        pass

    time.sleep(5)
else:
    print("Timed out. Check the dashboard for results.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Step 3: Read the analysis results
# ---------------------------------------------------------------------------

print("Step 3: Reading call analysis...")
print()

try:
    result_response = requests.get(
        "{}/calls/{}".format(BASE_URL, call_id),
        headers=headers,
        timeout=15,
    )
    result_response.raise_for_status()
    result = result_response.json()
except requests.exceptions.RequestException as e:
    print("Error reading results: {}".format(e))
    sys.exit(1)

analysis = result.get("analysis", {})
summary = result.get("summary", "")

print("Call Summary:")
if summary:
    print("  {}".format(summary))
else:
    print("  (No summary available)")
print()

print("Extracted Data:")
for key, value in analysis.items():
    print("  {}: {}".format(key, value))
print()

# ---------------------------------------------------------------------------
# Step 4: Send an SMS follow-up based on the call outcome
# ---------------------------------------------------------------------------

print("Step 4: Sending SMS follow-up...")
print()

# Build a personalized SMS message based on what was discussed in the call.
customer_name = analysis.get("customer_name", "there")
wants_changes = analysis.get("wants_changes")
requested_changes = analysis.get("requested_changes")
interested_in_bundle = analysis.get("interested_in_bundle")
has_questions = analysis.get("has_questions")
question_summary = analysis.get("question_summary")

# Start with a greeting.
sms_lines = [
    "Hi {}! This is Jamie from Greenfield Insurance.".format(customer_name),
    "Thanks for chatting about your policy renewal today.",
]

# Add context based on the call outcome.
if wants_changes and requested_changes:
    sms_lines.append(
        "I have noted your requested changes: {}. "
        "Our team will update your policy and send a revised quote "
        "within 1 business day.".format(requested_changes)
    )
elif wants_changes is False:
    sms_lines.append(
        "Your current coverage will renew as-is next month. "
        "No action needed on your end."
    )

if interested_in_bundle == "true" or interested_in_bundle is True:
    sms_lines.append(
        "I will also have our team put together a bundle quote "
        "for home + auto. We will email that over shortly."
    )

if has_questions and question_summary:
    sms_lines.append(
        "Regarding your question about {}, I will have a specialist "
        "follow up with more details.".format(question_summary)
    )

sms_lines.append(
    "Reply to this text anytime if you need anything else!"
)

sms_message = " ".join(sms_lines)

# Send the SMS.
sms_payload = {
    "phone_number": TO_NUMBER,
    "from": FROM_NUMBER,
    "message": sms_message,
}

print("SMS Message:")
print("  {}".format(sms_message))
print()

try:
    sms_response = requests.post(
        "{}/sms/send".format(BASE_URL),
        json=sms_payload,
        headers=headers,
        timeout=30,
    )
    sms_response.raise_for_status()

    print("SMS sent successfully!")
    print("Response: {}".format(json.dumps(sms_response.json(), indent=2)))
    print()

except requests.exceptions.RequestException as e:
    print("Error sending SMS: {}".format(e))
    if hasattr(e, "response") and e.response is not None:
        print("Response: {}".format(e.response.text))
    print()
    print("Note: SMS is an Enterprise feature. If you see a 403 error,")
    print("contact Bland support to enable SMS on your account.")
    print()

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

print("=" * 60)
print("WORKFLOW COMPLETE")
print("=" * 60)
print()
print("  1. Phone call completed (Call ID: {})".format(call_id))
print("  2. Structured data extracted via analysis_schema")
print("  3. Personalized SMS follow-up sent to {}".format(TO_NUMBER))
print()
print("This workflow can run automatically via webhooks in production.")
print("When the call webhook fires, your server reads the analysis data")
print("and sends the SMS follow-up immediately, with no polling needed.")
print()
print("Done.")
