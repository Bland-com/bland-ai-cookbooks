"""
Bland AI - Send a Call with Citation Schemas and Auto-Schedule Follow-Ups (Python)

This script demonstrates the full citation workflow:
  1. Send a call with citation_schema_ids so Bland extracts structured data
     from the conversation automatically.
  2. Wait for the call to complete and poll for results.
  3. Read the citation data that comes back, which includes the extracted
     fields and links each value to the exact utterance where it was mentioned.
  4. Based on the extracted data, automatically schedule a follow-up call
     and send an SMS confirmation.

Citation schemas let you define fields (like customer_name, email,
follow_up_date) that the AI extracts from the transcript after the call.
Each extracted value is paired with a "citation" pointing to the specific
part of the conversation where the information came from. This makes
your post-call data auditable and trustworthy.

Usage:
    1. Copy .env.example to .env and fill in your API key and phone number.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python call_with_citations.py

The script will:
    - Send a call with a citation schema attached
    - Poll until the call completes
    - Display the extracted citation data
    - Demonstrate how to auto-schedule a follow-up based on the results
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

# The phone number to call, in E.164 format (e.g., +15551234567).
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

# Optional: Your SMS-configured Bland phone number for sending follow-up texts.
# If not set, the SMS follow-up step is skipped.
FROM_NUMBER = os.getenv("FROM_NUMBER")

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
    print("Add the phone number to call in E.164 format to .env.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# HTTP headers (reused for all requests)
# ---------------------------------------------------------------------------

# Bland uses a simple API key in the Authorization header
# (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# Step 1: Understand citation schemas
# ---------------------------------------------------------------------------

# Citation schemas define the structured fields you want extracted from every
# call. You create them once in the Bland dashboard (or via the API), then
# reference them by ID when sending calls.
#
# Each schema has an array of fields. Each field specifies:
#   - name: The field name (e.g., "customer_email")
#   - type: "string", "integer", "boolean", or "enum"
#   - description: Instructions for the AI on what to extract
#
# After the call, Bland returns:
#   - analysis: An object with each field name as a key and the extracted
#     value as the value.
#   - citations: An array linking each extracted value to the specific
#     transcript utterance where the information was mentioned. This is
#     what makes citations powerful: you can trace every piece of data
#     back to the exact moment in the conversation.
#
# For this example, we will use the analysis_schema parameter directly
# on the call (which works the same way as citation_schema_ids, but is
# defined inline rather than referencing a pre-created schema).

print("=" * 60)
print("CALL WITH CITATIONS AND AUTO FOLLOW-UP")
print("=" * 60)
print()

# ---------------------------------------------------------------------------
# Step 2: Send the call with an analysis schema
# ---------------------------------------------------------------------------

# The agent prompt instructs the AI to collect specific information during
# the call. The analysis_schema (or citation_schema_ids) tells Bland which
# fields to extract from the transcript after the call ends.

AGENT_PROMPT = """You are Alex, a friendly follow-up specialist at CloudSync Software.
You are calling a customer who recently signed up for a free trial.

Your goals:
1. Introduce yourself and thank them for trying CloudSync.
2. Ask how their experience has been so far.
3. Find out if they have any questions about the product.
4. Ask if they would like to schedule a follow-up call or demo with a product specialist.
5. If they want a follow-up, ask for their preferred date and time.
6. Collect their email address for sending a calendar invite.
7. Thank them and wrap up.

Keep the conversation natural and friendly. Do not rush. Listen to their
feedback and respond thoughtfully. If they are not interested in a follow-up,
thank them and let them know they can reach out anytime.

Important: Make sure to ask for their email and preferred follow-up time
so we can schedule the next touchpoint."""

# The analysis schema defines what to extract from the conversation.
# Each field maps to a specific piece of information the agent should collect.
# After the call, Bland's AI reads the transcript and fills in these fields.
analysis_schema = {
    # String field: the customer's full name, extracted from the conversation.
    "customer_name": "The customer's full name as mentioned during the call.",

    # String field: their email address for follow-up communication.
    "customer_email": "The customer's email address.",

    # String field: when they want the follow-up call.
    "preferred_follow_up_time": (
        "The customer's preferred date and time for a follow-up call. "
        "Format as a human-readable string like 'Tuesday at 2 PM' or "
        "'March 20th at 10 AM'. Return null if they declined a follow-up."
    ),

    # Boolean field: did they agree to a follow-up?
    "wants_follow_up": (
        "Whether the customer agreed to schedule a follow-up call or demo. "
        "true if yes, false if no."
    ),

    # String field: overall sentiment from the conversation.
    "customer_sentiment": (
        "The customer's overall sentiment about the product. "
        "One of: positive, neutral, or negative."
    ),

    # String field: a concise summary of their feedback.
    "feedback_summary": (
        "A one to two sentence summary of the customer's feedback "
        "about their experience with CloudSync."
    ),
}

# Build the call payload.
call_payload = {
    # The phone number to call.
    "phone_number": PHONE_NUMBER,

    # The agent prompt that drives the conversation.
    "task": AGENT_PROMPT,

    # The analysis schema that defines what to extract after the call.
    # This is the inline version. If you have pre-created citation schemas
    # in the Bland dashboard, you would use citation_schema_ids instead:
    #
    #   "citation_schema_ids": ["schema-uuid-1", "schema-uuid-2"]
    #
    # Both approaches produce the same result: structured extracted data
    # with citations linking each value to its source in the transcript.
    "analysis_schema": analysis_schema,

    # Record the call so we can verify the transcript later.
    "record": True,

    # Limit the call to 5 minutes for this demo.
    "max_duration": 5,

    # Request the citations webhook event so we get citation data
    # in the post-call webhook payload.
    "webhook_events": ["citations"],

    # A custom summary prompt to get a follow-up-focused summary.
    "summary_prompt": (
        "Summarize this call in three bullet points: "
        "(1) the customer's overall feedback, "
        "(2) whether they want a follow-up and when, "
        "(3) any action items for the team."
    ),
}

print("Sending call to {}...".format(PHONE_NUMBER))
print()

try:
    response = requests.post(
        "{}/calls".format(BASE_URL),
        json=call_payload,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
except requests.exceptions.RequestException as e:
    print("Error sending call: {}".format(e))
    if hasattr(e, "response") and e.response is not None:
        print("Response: {}".format(e.response.text))
    sys.exit(1)

call_data = response.json()
call_id = call_data.get("call_id")

if not call_id:
    print("Error: No call_id in response.")
    print("Response: {}".format(json.dumps(call_data, indent=2)))
    sys.exit(1)

print("Call queued successfully!")
print("  Call ID: {}".format(call_id))
print()

# ---------------------------------------------------------------------------
# Step 3: Poll for call completion
# ---------------------------------------------------------------------------

# After sending the call, we poll the call details endpoint until the call
# completes. In production, you would use a webhook instead of polling.
# We poll here to keep the example self-contained.

print("Waiting for the call to complete...")
print("(Answer your phone when it rings!)")
print()

MAX_POLL_ATTEMPTS = 60  # Poll for up to 5 minutes (60 * 5 seconds)
POLL_INTERVAL = 5       # Seconds between polls

for attempt in range(MAX_POLL_ATTEMPTS):
    try:
        poll_response = requests.get(
            "{}/calls/{}".format(BASE_URL, call_id),
            headers=headers,
            timeout=15,
        )
        poll_response.raise_for_status()
        poll_data = poll_response.json()

        status = poll_data.get("status", "unknown")
        completed = poll_data.get("completed", False)

        if completed or status == "completed":
            print("Call completed!")
            print()
            break

        # Show a progress indicator.
        elapsed = (attempt + 1) * POLL_INTERVAL
        print("  Still in progress... ({}s elapsed, status: {})".format(
            elapsed, status
        ))

    except requests.exceptions.RequestException:
        pass  # Ignore transient errors during polling

    time.sleep(POLL_INTERVAL)
else:
    print("Timed out waiting for the call to complete.")
    print("You can still check the results later using:")
    print("  python analyze_call.py {}".format(call_id))
    sys.exit(0)

# ---------------------------------------------------------------------------
# Step 4: Display call results and citations
# ---------------------------------------------------------------------------

# Fetch the final call data with all analysis results.
try:
    final_response = requests.get(
        "{}/calls/{}".format(BASE_URL, call_id),
        headers=headers,
        timeout=15,
    )
    final_response.raise_for_status()
    call_result = final_response.json()
except requests.exceptions.RequestException as e:
    print("Error fetching final call data: {}".format(e))
    sys.exit(1)

# Display basic call info.
print("=" * 60)
print("CALL RESULTS")
print("=" * 60)
print()
print("  Call ID:       {}".format(call_result.get("call_id", "N/A")))
print("  Duration:      {} min".format(call_result.get("call_length", "N/A")))
print("  Ended By:      {}".format(call_result.get("call_ended_by", "N/A")))
print("  Cost:          ${}".format(call_result.get("price", "N/A")))
print()

# Display the AI-generated summary.
summary = call_result.get("summary", "")
if summary:
    print("Summary:")
    for line in summary.split("\n"):
        print("  {}".format(line))
    print()

# Display the analysis results (extracted fields from the citation schema).
# This is where the structured data lives. Each key corresponds to a field
# you defined in the analysis_schema (or citation_schema_ids).
analysis = call_result.get("analysis", {})
if analysis:
    print("=" * 60)
    print("EXTRACTED DATA (from analysis schema)")
    print("=" * 60)
    print()
    for field_name, field_value in analysis.items():
        print("  {}: {}".format(field_name, field_value))
    print()
else:
    print("No analysis data available yet.")
    print("Analysis data may take a few seconds to populate after the call.")
    print("Try running: python analyze_call.py {}".format(call_id))
    print()

# Display citations if available.
# Citations link each extracted value to the specific utterance in the
# transcript where the information was mentioned. This is what makes
# citation schemas more powerful than plain analysis: you get provenance
# for every piece of data.
#
# Citation format:
# {
#   "field": "customer_email",
#   "value": "alex@example.com",
#   "utterance": "Sure, my email is alex@example.com.",
#   "speaker": "user",
#   "timestamp": "2024-01-15T10:31:25.000Z",
#   "confidence": 0.95
# }
citations = call_result.get("citations", [])
if citations:
    print("=" * 60)
    print("CITATIONS (linking data to transcript)")
    print("=" * 60)
    print()
    print("Each citation shows where a piece of extracted data came from")
    print("in the conversation, so you can verify and audit the results.")
    print()

    for i, citation in enumerate(citations):
        print("  Citation {}:".format(i + 1))

        # The field name this citation relates to.
        field = citation.get("field", citation.get("key", "unknown"))
        print("    Field:      {}".format(field))

        # The extracted value for this field.
        value = citation.get("value", "N/A")
        print("    Value:      {}".format(value))

        # The exact utterance where this information was mentioned.
        utterance = citation.get("utterance", citation.get("text", "N/A"))
        print("    Utterance:  \"{}\"".format(utterance))

        # Who said it: "user" (the customer) or "agent" (the AI).
        speaker = citation.get("speaker", "N/A")
        print("    Speaker:    {}".format(speaker))

        # Confidence score (0 to 1) for the extraction.
        confidence = citation.get("confidence")
        if confidence is not None:
            print("    Confidence: {:.0%}".format(confidence))

        print()
else:
    print("No citations available yet.")
    print("Citations arrive in the delayed webhook (30 to 60 seconds after")
    print("the call). You can also check the call details in the dashboard.")
    print()

# ---------------------------------------------------------------------------
# Step 5: Auto-schedule a follow-up based on extracted data
# ---------------------------------------------------------------------------

# This is the payoff of using citation schemas: you get clean, structured
# data that you can act on programmatically. Here we check if the customer
# wants a follow-up and, if so, schedule one automatically.

print("=" * 60)
print("AUTO FOLLOW-UP SCHEDULING")
print("=" * 60)
print()

wants_follow_up = analysis.get("wants_follow_up")
follow_up_time = analysis.get("preferred_follow_up_time")
customer_name = analysis.get("customer_name", "the customer")
customer_email = analysis.get("customer_email")

if wants_follow_up and follow_up_time:
    print("The customer wants a follow-up!")
    print("  Name:           {}".format(customer_name))
    print("  Email:          {}".format(customer_email or "N/A"))
    print("  Preferred Time: {}".format(follow_up_time))
    print()

    # -----------------------------------------------------------------------
    # Schedule a follow-up call
    # -----------------------------------------------------------------------

    # In production, you would parse the follow_up_time into a proper
    # datetime and pass it as start_time. For this demo, we show the
    # structure of the request without actually sending it.

    follow_up_payload = {
        "phone_number": PHONE_NUMBER,
        "task": (
            "You are Alex from CloudSync Software, calling back {} "
            "for a scheduled product demo. They signed up for a free trial "
            "and expressed interest in learning more. Walk them through "
            "the key features and answer any questions they have. "
            "Their feedback from the last call: {}"
        ).format(
            customer_name,
            analysis.get("feedback_summary", "No prior feedback recorded."),
        ),
        "max_duration": 15,
        "record": True,
        # In production, parse the preferred time and set start_time:
        # "start_time": "2026-03-20 14:00:00 -05:00",
        "request_data": {
            "customer_name": customer_name,
            "customer_email": customer_email or "",
            "original_call_id": call_id,
        },
        "analysis_schema": {
            "demo_completed": "Was the product demo completed successfully? true or false.",
            "interested_in_purchase": "Is the customer interested in purchasing? true or false.",
            "plan_discussed": "Which plan was discussed? starter, professional, enterprise, or none.",
            "next_steps": "What are the agreed next steps after this call?",
        },
    }

    print("Follow-up call payload (ready to send):")
    print(json.dumps(follow_up_payload, indent=2))
    print()

    # Uncomment the lines below to actually send the follow-up call:
    # follow_up_response = requests.post(
    #     "{}/calls".format(BASE_URL),
    #     json=follow_up_payload,
    #     headers=headers,
    #     timeout=30,
    # )
    # follow_up_data = follow_up_response.json()
    # print("Follow-up call scheduled! Call ID: {}".format(
    #     follow_up_data.get("call_id")
    # ))

    # -----------------------------------------------------------------------
    # Send an SMS confirmation (if FROM_NUMBER is configured)
    # -----------------------------------------------------------------------

    if FROM_NUMBER:
        sms_message = (
            "Hi {}! This is Alex from CloudSync. Thanks for chatting today. "
            "As discussed, we have your follow-up demo scheduled for {}. "
            "Looking forward to it! Reply to this text if you need to reschedule."
        ).format(customer_name, follow_up_time)

        sms_payload = {
            "phone_number": PHONE_NUMBER,
            "from": FROM_NUMBER,
            "message": sms_message,
        }

        print("SMS confirmation payload (ready to send):")
        print(json.dumps(sms_payload, indent=2))
        print()

        # Uncomment to actually send the SMS:
        # sms_response = requests.post(
        #     "{}/sms/send".format(BASE_URL),
        #     json=sms_payload,
        #     headers=headers,
        #     timeout=30,
        # )
        # print("SMS confirmation sent!")
    else:
        print("Skipping SMS confirmation (FROM_NUMBER not set in .env).")
        print("Set FROM_NUMBER to an SMS-configured Bland number to enable this.")
        print()

elif wants_follow_up is False:
    print("The customer declined a follow-up call.")
    print("No follow-up scheduled. Their feedback has been recorded:")
    print("  Sentiment: {}".format(analysis.get("customer_sentiment", "N/A")))
    print("  Feedback:  {}".format(analysis.get("feedback_summary", "N/A")))
    print()
else:
    print("Could not determine follow-up preference from the call data.")
    print("This may happen if the call was very short or the analysis is")
    print("still processing. Check the dashboard for full results.")
    print()

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

print("=" * 60)
print("WHAT YOU LEARNED")
print("=" * 60)
print()
print("  1. How to attach an analysis_schema (or citation_schema_ids)")
print("     to a call so Bland extracts structured data automatically.")
print()
print("  2. How citations link each extracted value back to the exact")
print("     utterance in the transcript, making the data auditable.")
print()
print("  3. How to use the extracted data to auto-schedule follow-up")
print("     calls and send SMS confirmations without manual work.")
print()
print("  In production, replace polling with webhooks for real-time")
print("  processing. See the webhook_listener scripts in this cookbook.")
print()
print("Done.")
