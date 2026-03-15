"""
webhook_receiver.py
===================
Speed to Lead: Flask webhook server for receiving lead form submissions
and post-call results from Bland AI.

This server exposes two endpoints:

  POST /webhook/lead-form
      Receives new lead data from your website form (or a form builder like
      Typeform, HubSpot, etc.) and immediately triggers a Bland AI call to
      that lead. This is the core of speed to lead: the lead fills out a
      form and their phone rings within seconds.

  POST /webhook/call-complete
      Receives post-call data from Bland AI after each call finishes. This
      includes the full transcript, summary, recording URL, call duration,
      and any variables extracted during the conversation. Use this data to
      update your CRM, score leads, and trigger follow-up actions.

Usage:
    1. Copy .env.example to .env and add your credentials.
    2. Install dependencies: pip install requests flask python-dotenv
    3. Run: python webhook_receiver.py
    4. The server starts on http://localhost:5000
    5. For production or testing with Bland webhooks, expose with ngrok:
       ngrok http 5000

Dependencies:
    pip install requests flask python-dotenv
"""

import os
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Import the call_lead function from lead_caller.py in the same directory.
# This handles all the Bland AI call logic so we do not duplicate it here.
from lead_caller import call_lead

# ---------------------------------------------------------------------------
# Load environment variables from the .env file.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Create the Flask application.
# ---------------------------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory storage for tracking leads and call results.
# In production, replace this with a real database (PostgreSQL, MongoDB, etc.)
# or push data directly to your CRM.
# ---------------------------------------------------------------------------
leads_db = []
call_results_db = []


# ===========================================================================
# Helper Functions
# ===========================================================================

def log_event(event_type, data):
    """
    Log an event with a timestamp for debugging.

    In production, you would replace this with a proper logging framework
    (e.g., Python's logging module, Datadog, Sentry, etc.).

    Args:
        event_type (str): A label for the event (e.g., "NEW_LEAD", "CALL_COMPLETE").
        data (dict): The event data to log.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    print()
    print("=" * 60)
    print(f"[{timestamp}] {event_type}")
    print("=" * 60)
    print(json.dumps(data, indent=2, default=str))
    print()


def validate_lead_data(data):
    """
    Validate that the incoming lead data has all required fields.

    This prevents calling the Bland API with incomplete data, which would
    result in an error or a poorly personalized call.

    Args:
        data (dict): The incoming lead form data.

    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """

    # Define the required fields and friendly error messages.
    required_fields = {
        "name": "Lead name is required.",
        "phone": "Lead phone number is required.",
        "email": "Lead email is required.",
    }

    # Check each required field.
    for field, error_msg in required_fields.items():
        if not data.get(field):
            return False, error_msg

    # Basic phone number format check. E.164 format requires a leading "+".
    phone = data.get("phone", "")
    if not phone.startswith("+"):
        return False, (
            "Phone number must be in E.164 format (e.g., +15551234567). "
            "It must start with a + followed by the country code."
        )

    return True, None


def push_to_crm(lead_data, call_data):
    """
    Push lead and call data to your CRM.

    This is a placeholder function. Replace the contents with actual API
    calls to your CRM (Salesforce, HubSpot, Pipedrive, Close, etc.).

    Args:
        lead_data (dict): The original lead form data.
        call_data (dict): The post-call data from Bland AI.
    """

    # -----------------------------------------------------------------------
    # PLACEHOLDER: Replace this section with your actual CRM integration.
    #
    # Example for HubSpot:
    #   import requests
    #   hubspot_url = "https://api.hubapi.com/crm/v3/objects/contacts"
    #   headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}"}
    #   contact_data = {
    #       "properties": {
    #           "firstname": lead_data.get("name", "").split()[0],
    #           "lastname": " ".join(lead_data.get("name", "").split()[1:]),
    #           "email": lead_data.get("email"),
    #           "phone": lead_data.get("phone"),
    #           "lead_status": "QUALIFIED" if call_data.get("qualified") else "UNQUALIFIED",
    #           "notes": call_data.get("summary", ""),
    #       }
    #   }
    #   requests.post(hubspot_url, json=contact_data, headers=headers)
    #
    # Example for Salesforce:
    #   from simple_salesforce import Salesforce
    #   sf = Salesforce(username=..., password=..., security_token=...)
    #   sf.Lead.create({
    #       "FirstName": lead_data.get("name", "").split()[0],
    #       "LastName": " ".join(lead_data.get("name", "").split()[1:]),
    #       "Email": lead_data.get("email"),
    #       "Phone": lead_data.get("phone"),
    #       "Status": "Qualified" if call_data.get("qualified") else "Open",
    #       "Description": call_data.get("summary", ""),
    #   })
    # -----------------------------------------------------------------------

    print("[CRM] Would push the following data to CRM:")
    print(f"  Lead: {lead_data.get('name')} ({lead_data.get('email')})")
    print(f"  Call ID: {call_data.get('call_id', 'N/A')}")
    print(f"  Status: {call_data.get('status', 'N/A')}")
    print(f"  Answered by: {call_data.get('answered_by', 'N/A')}")
    print(f"  Summary: {call_data.get('summary', 'N/A')[:100]}...")
    print()


# ===========================================================================
# Routes
# ===========================================================================

@app.route("/webhook/lead-form", methods=["POST"])
def handle_lead_form():
    """
    POST /webhook/lead-form

    Receives a new lead form submission and immediately triggers a Bland AI
    call to qualify the lead. This is the speed-to-lead endpoint: the time
    between form submission and phone ringing should be under 10 seconds.

    Expected JSON body:
    {
        "name": "Jane Smith",
        "phone": "+15551234567",
        "email": "jane@example.com",
        "source": "Website Contact Form",   (optional, defaults to "Direct")
        "interest": "Enterprise Plan"        (optional, defaults to "General Inquiry")
    }

    Returns:
        201: Call successfully queued with call_id.
        400: Missing or invalid lead data.
        500: Bland API call failed.
    """

    # -----------------------------------------------------------------------
    # Parse the incoming JSON body.
    # -----------------------------------------------------------------------
    data = request.get_json()

    # If the request body is not valid JSON, return an error.
    if not data:
        return jsonify({
            "error": "Request body must be valid JSON.",
        }), 400

    # -----------------------------------------------------------------------
    # Log the incoming lead for debugging.
    # -----------------------------------------------------------------------
    log_event("NEW_LEAD_RECEIVED", data)

    # -----------------------------------------------------------------------
    # Validate required fields (name, phone, email).
    # -----------------------------------------------------------------------
    is_valid, error_message = validate_lead_data(data)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    # -----------------------------------------------------------------------
    # Extract lead fields with sensible defaults for optional fields.
    # -----------------------------------------------------------------------
    name = data["name"]
    phone = data["phone"]
    email = data["email"]

    # "source" tells the agent where the lead came from, so it can reference
    # it in the conversation (e.g., "I saw you filled out our website form").
    source = data.get("source", "Direct")

    # "interest" tells the agent what the lead was looking at, so the
    # conversation starts with relevant context.
    interest = data.get("interest", "General Inquiry")

    # -----------------------------------------------------------------------
    # Store the lead in our in-memory database.
    # In production, save this to your actual database or CRM.
    # -----------------------------------------------------------------------
    lead_record = {
        "name": name,
        "phone": phone,
        "email": email,
        "source": source,
        "interest": interest,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "call_id": None,        # Will be filled after the Bland API responds
        "call_status": None,    # Will be updated when the call completes
    }

    # -----------------------------------------------------------------------
    # Immediately trigger a Bland AI call to the lead.
    # This is the core of speed to lead. The call_lead() function sends
    # the API request and returns almost instantly (the call itself is
    # placed asynchronously by Bland's infrastructure).
    # -----------------------------------------------------------------------
    print(f"Triggering instant call to {name} at {phone}...")
    result = call_lead(name, phone, email, source, interest)

    # -----------------------------------------------------------------------
    # Handle the API response.
    # -----------------------------------------------------------------------
    if result and result.get("status") == "success":
        # The call was successfully queued. Save the call_id for tracking.
        call_id = result.get("call_id", "unknown")
        lead_record["call_id"] = call_id

        # Store the lead record.
        leads_db.append(lead_record)

        log_event("CALL_QUEUED", {
            "lead_name": name,
            "phone": phone,
            "call_id": call_id,
        })

        return jsonify({
            "status": "success",
            "message": f"Call queued for {name}. Phone will ring within seconds.",
            "call_id": call_id,
        }), 201

    else:
        # The Bland API returned an error. Log it and return the error.
        error_detail = result if result else {"error": "No response from Bland API"}

        log_event("CALL_FAILED", {
            "lead_name": name,
            "phone": phone,
            "error": error_detail,
        })

        return jsonify({
            "status": "error",
            "message": "Failed to queue the call. Check server logs for details.",
            "detail": error_detail,
        }), 500


@app.route("/webhook/call-complete", methods=["POST"])
def handle_call_complete():
    """
    POST /webhook/call-complete

    Receives post-call data from Bland AI after a qualification call finishes.
    This webhook is triggered automatically by Bland when the call ends.

    The payload includes:
    - call_id: Unique identifier for the call
    - status: "completed", "failed", "no-answer", etc.
    - answered_by: "human" or "voicemail"
    - call_length: Duration in minutes
    - transcripts: Array of transcript objects with speaker labels
    - concatenated_transcript: Full transcript as a single string
    - summary: AI-generated summary of the conversation
    - variables: Any variables extracted during the call
    - recording_url: URL to the call recording (if recording was enabled)
    - price: Cost of the call in USD

    This endpoint processes the results and pushes them to your CRM.

    Returns:
        200: Results received and processed.
    """

    # -----------------------------------------------------------------------
    # Parse the incoming webhook payload from Bland AI.
    # -----------------------------------------------------------------------
    data = request.get_json()

    if not data:
        return jsonify({"error": "Empty webhook payload."}), 400

    # -----------------------------------------------------------------------
    # Log the full webhook payload for debugging.
    # -----------------------------------------------------------------------
    log_event("CALL_COMPLETE_WEBHOOK", data)

    # -----------------------------------------------------------------------
    # Extract key fields from the webhook payload.
    # -----------------------------------------------------------------------
    call_id = data.get("call_id", "unknown")
    status = data.get("status", "unknown")
    answered_by = data.get("answered_by", "unknown")
    call_length = data.get("call_length", 0)
    transcript = data.get("concatenated_transcript", "")
    summary = data.get("summary", "")
    variables = data.get("variables", {})
    recording_url = data.get("recording_url", "")
    price = data.get("price", 0)

    # -----------------------------------------------------------------------
    # Determine if the lead was qualified based on the call outcome.
    # You can customize this logic based on the variables your prompt
    # instructs the AI to extract during the conversation.
    # -----------------------------------------------------------------------
    is_qualified = variables.get("qualified", False)
    was_transferred = variables.get("transferred", False)
    budget = variables.get("budget", "Not discussed")
    timeline = variables.get("timeline", "Not discussed")

    # -----------------------------------------------------------------------
    # Build a structured result record.
    # -----------------------------------------------------------------------
    call_result = {
        "call_id": call_id,
        "status": status,
        "answered_by": answered_by,
        "call_length_minutes": call_length,
        "summary": summary,
        "is_qualified": is_qualified,
        "was_transferred": was_transferred,
        "budget": budget,
        "timeline": timeline,
        "recording_url": recording_url,
        "price_usd": price,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    # Store the result in memory.
    call_results_db.append(call_result)

    # -----------------------------------------------------------------------
    # Log a human-readable summary of the call outcome.
    # -----------------------------------------------------------------------
    print()
    print("-" * 60)
    print("CALL RESULT SUMMARY")
    print("-" * 60)
    print(f"  Call ID:       {call_id}")
    print(f"  Status:        {status}")
    print(f"  Answered by:   {answered_by}")
    print(f"  Duration:      {call_length} minutes")
    print(f"  Qualified:     {'Yes' if is_qualified else 'No'}")
    print(f"  Transferred:   {'Yes' if was_transferred else 'No'}")
    print(f"  Budget:        {budget}")
    print(f"  Timeline:      {timeline}")
    print(f"  Cost:          ${price:.4f}")
    print(f"  Recording:     {recording_url or 'N/A'}")
    print()
    print(f"  Summary: {summary[:200]}{'...' if len(summary) > 200 else ''}")
    print("-" * 60)
    print()

    # -----------------------------------------------------------------------
    # Find the matching lead record and update it with call results.
    # This connects the original lead data with the call outcome.
    # -----------------------------------------------------------------------
    matching_lead = None
    for lead in leads_db:
        if lead.get("call_id") == call_id:
            lead["call_status"] = status
            lead["answered_by"] = answered_by
            lead["is_qualified"] = is_qualified
            matching_lead = lead
            break

    # -----------------------------------------------------------------------
    # Push results to your CRM.
    # The push_to_crm function is a placeholder. Replace it with actual
    # API calls to Salesforce, HubSpot, Pipedrive, or your CRM of choice.
    # -----------------------------------------------------------------------
    if matching_lead:
        push_to_crm(matching_lead, call_result)
    else:
        # If we do not have a matching lead (e.g., the server restarted),
        # still log the CRM push with available data.
        push_to_crm({"name": "Unknown", "email": "Unknown"}, call_result)

    # -----------------------------------------------------------------------
    # Handle different call outcomes with specific follow-up actions.
    # -----------------------------------------------------------------------
    if answered_by == "voicemail":
        # The lead did not answer. Schedule a follow-up or send an email.
        print("[ACTION] Lead went to voicemail. Consider scheduling a retry call.")
        print("         You could use the Bland batch API to retry in 30 minutes.")

    elif is_qualified and not was_transferred:
        # The lead is qualified but was not transferred during the call.
        # This might happen if the sales rep was unavailable.
        print("[ACTION] Qualified lead was not transferred.")
        print("         Notify sales team immediately for a manual follow-up.")

    elif is_qualified and was_transferred:
        # Best case: the lead was qualified and transferred to a sales rep.
        print("[ACTION] Qualified lead was transferred to sales. Update CRM status.")

    else:
        # The lead was not qualified. Send nurture content.
        print("[ACTION] Lead was not qualified. Add to email nurture sequence.")

    # -----------------------------------------------------------------------
    # Return a 200 OK to acknowledge receipt of the webhook.
    # Bland expects a 200 response. If you return an error, Bland may
    # retry the webhook delivery.
    # -----------------------------------------------------------------------
    return jsonify({
        "status": "received",
        "call_id": call_id,
        "processed": True,
    }), 200


@app.route("/health", methods=["GET"])
def health_check():
    """
    GET /health

    Simple health check endpoint for monitoring. Returns the number of
    leads received and calls completed since the server started.
    """
    return jsonify({
        "status": "healthy",
        "leads_received": len(leads_db),
        "calls_completed": len(call_results_db),
    }), 200


# ===========================================================================
# Main: Start the Flask development server.
# ===========================================================================
if __name__ == "__main__":
    # -----------------------------------------------------------------------
    # Print startup information.
    # -----------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Speed to Lead Webhook Server (Python / Flask)")
    print("=" * 60)
    print()
    print("Endpoints:")
    print("  POST /webhook/lead-form      Receive lead form submissions")
    print("  POST /webhook/call-complete   Receive post-call results from Bland")
    print("  GET  /health                  Health check")
    print()
    print("For local testing with Bland webhooks, expose with ngrok:")
    print("  ngrok http 5000")
    print()
    print("Then update WEBHOOK_URL in .env with your ngrok HTTPS URL:")
    print("  https://your-id.ngrok.io/webhook/call-complete")
    print()
    print("=" * 60)
    print()

    # Start the Flask development server.
    # In production, use a WSGI server like Gunicorn or uWSGI:
    #   gunicorn webhook_receiver:app -b 0.0.0.0:5000 -w 4
    app.run(
        host="0.0.0.0",    # Listen on all interfaces (required for Docker/ngrok)
        port=5000,          # Default Flask port
        debug=True,         # Enable auto-reload and detailed error pages (disable in production)
    )
