"""
Bland AI - Webhook Listener (Python)

This script runs a Flask server that listens for post-call webhook payloads
from Bland AI. When a call completes, Bland sends a POST request to your
webhook URL with the full call data. This script receives that data, logs
key information, and demonstrates how you would process and store it.

Usage:
    1. Copy .env.example to .env and fill in your API key (optional for webhooks).
    2. Install dependencies: pip install requests python-dotenv flask
    3. Run: python webhook_listener.py
    4. The server starts on port 3000 (or the PORT in your .env).
    5. Expose the server to the internet using ngrok or a similar tool:
           ngrok http 3000
    6. Copy the ngrok HTTPS URL and use it as the webhook parameter when
       creating calls:
           "webhook": "https://abc123.ngrok.io/webhook/call-complete"

The server handles two types of webhook payloads:
    - Immediate payload: Arrives right when the call ends. Contains the
      transcript, summary, variables, disposition, and basic metadata.
    - Delayed payload: Arrives 30 to 60 seconds later. Contains the
      corrected transcript with confidence scores and citation data.
"""

import os
import json
from datetime import datetime

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from .env file.
load_dotenv()

# Port for the Flask server. Defaults to 3000 if not set.
PORT = int(os.getenv("PORT", "3000"))

# ---------------------------------------------------------------------------
# Flask app setup
# ---------------------------------------------------------------------------

# Create the Flask application instance.
app = Flask(__name__)

# ---------------------------------------------------------------------------
# In-memory storage (placeholder for a real database)
# ---------------------------------------------------------------------------

# In production, you would store webhook payloads in a database (PostgreSQL,
# MongoDB, etc.). This dictionary simulates that by storing payloads in memory,
# keyed by call_id. It resets when the server restarts.
call_store = {}


def save_call_data(call_id, data):
    """
    Save call data to the in-memory store.

    In production, replace this with your actual database logic. For example:
        - Insert a row into a PostgreSQL table
        - Save a document in MongoDB
        - Push to a message queue for async processing

    Args:
        call_id: The unique identifier for the call.
        data: The full webhook payload dictionary.
    """
    call_store[call_id] = data
    print("  [DB] Saved call {} to store. Total calls stored: {}".format(
        call_id, len(call_store)
    ))


def update_call_data(call_id, updates):
    """
    Merge additional data into an existing call record.

    This is used when the delayed webhook arrives with corrected transcript
    and citation data. The delayed payload should be merged with the
    immediate payload using the call_id as the key.

    Args:
        call_id: The unique identifier for the call.
        updates: A dictionary of fields to merge into the existing record.
    """
    if call_id in call_store:
        call_store[call_id].update(updates)
        print("  [DB] Updated call {} with additional data.".format(call_id))
    else:
        # If the immediate payload has not arrived yet (unlikely but possible),
        # store the delayed data as its own record.
        call_store[call_id] = updates
        print("  [DB] Stored delayed data for call {} (no immediate data found).".format(
            call_id
        ))


# ---------------------------------------------------------------------------
# Webhook endpoint: POST /webhook/call-complete
# ---------------------------------------------------------------------------

@app.route("/webhook/call-complete", methods=["POST"])
def handle_call_complete():
    """
    Receives the post-call webhook from Bland AI.

    Bland sends two POST requests per call:
      1. Immediate payload (right when the call ends):
         Contains call_id, call_length, summary, transcripts, variables,
         disposition_tag, and other core fields.
      2. Delayed payload (30 to 60 seconds later):
         Contains corrected_transcript (with speaker labels and confidence
         scores) and citations (linking variables to utterances).

    This handler processes both types. It distinguishes them by checking
    whether the payload contains the "corrected_transcript" field.
    """
    # Get the raw JSON payload from the request body.
    payload = request.get_json(silent=True)

    # If the body is not valid JSON, return a 400 error.
    if payload is None:
        print("[WARN] Received webhook with no JSON body.")
        return jsonify({"error": "No JSON body provided"}), 400

    # Extract the call_id, which is present in both immediate and delayed payloads.
    call_id = payload.get("call_id", "unknown")

    # Print a timestamp for logging.
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if this is the delayed payload (contains corrected_transcript).
    if "corrected_transcript" in payload:
        # This is the delayed payload with corrected transcript and citations.
        print()
        print("=" * 60)
        print("[{}] DELAYED WEBHOOK RECEIVED".format(timestamp))
        print("=" * 60)
        print("  Call ID: {}".format(call_id))

        # The corrected transcript includes speaker labels and confidence scores.
        corrected = payload.get("corrected_transcript", {})
        if corrected:
            print()
            print("  Corrected Transcript:")
            # The corrected transcript may contain a "segments" array with
            # detailed utterance data including confidence and timestamps.
            segments = corrected.get("segments", [])
            if segments:
                for segment in segments[:5]:  # Show first 5 segments
                    speaker = segment.get("speaker", "unknown")
                    text = segment.get("text", "")
                    confidence = segment.get("confidence", 0)
                    print("    [{} (confidence: {:.0%})] {}".format(
                        speaker, confidence, text
                    ))
                if len(segments) > 5:
                    print("    ... and {} more segments.".format(len(segments) - 5))
            else:
                # Sometimes the corrected transcript is a simple string.
                print("    {}".format(json.dumps(corrected, indent=4)[:500]))

        # Citations link extracted variables to specific utterances in the
        # transcript, showing exactly where each piece of information came from.
        citations = payload.get("citations", [])
        if citations:
            print()
            print("  Citations:")
            for citation in citations[:5]:  # Show first 5 citations
                print("    {}".format(json.dumps(citation)))
            if len(citations) > 5:
                print("    ... and {} more citations.".format(len(citations) - 5))

        # Merge the delayed data into the existing call record.
        update_call_data(call_id, {
            "corrected_transcript": corrected,
            "citations": citations,
        })

    else:
        # This is the immediate payload with core call data.
        print()
        print("=" * 60)
        print("[{}] IMMEDIATE WEBHOOK RECEIVED".format(timestamp))
        print("=" * 60)

        # --- Basic call metadata ---
        print()
        print("  Call ID:       {}".format(call_id))
        print("  Completed:     {}".format(payload.get("completed", "N/A")))
        print("  Inbound:       {}".format(payload.get("inbound", "N/A")))
        print("  Call Length:    {} min".format(payload.get("call_length", "N/A")))
        print("  Price:         ${}".format(payload.get("price", "N/A")))
        print("  Ended By:      {}".format(payload.get("call_ended_by", "N/A")))
        print("  Error:         {}".format(payload.get("error_message") or "None"))

        # --- Disposition ---
        # The disposition_tag is the outcome label that the agent selected
        # from the dispositions list you configured on the call.
        # Example values: "Interested", "Not Interested", "Callback Requested"
        disposition = payload.get("disposition_tag")
        if disposition:
            print()
            print("  Disposition:   {}".format(disposition))

        # --- Transfer info ---
        # If the call was transferred to another number, these fields are populated.
        transferred_to = payload.get("transferred_to")
        if transferred_to:
            print()
            print("  Transferred To:         {}".format(transferred_to))
            print("  Pre-Transfer Duration:  {} min".format(
                payload.get("pre_transfer_duration", "N/A")
            ))
            print("  Post-Transfer Duration: {} min".format(
                payload.get("post_transfer_duration", "N/A")
            ))

        # --- Summary ---
        # The AI-generated summary of the call. This follows the format
        # specified by the summary_prompt parameter (if set), or uses
        # the default Bland summary format.
        summary = payload.get("summary", "")
        if summary:
            print()
            print("  Summary:")
            # Indent each line of the summary for readability.
            for line in summary.split("\n"):
                print("    {}".format(line))

        # --- Transcript ---
        # The concatenated transcript is the full conversation as a single
        # string with speaker labels (e.g., "Agent: ... User: ...").
        concatenated = payload.get("concatenated_transcript", "")
        if concatenated:
            print()
            print("  Transcript:")
            # Show a preview of the transcript (first 800 characters).
            preview = concatenated[:800]
            for line in preview.split("\n"):
                print("    {}".format(line))
            if len(concatenated) > 800:
                print("    ... (truncated, {} total characters)".format(
                    len(concatenated)
                ))

        # --- Variables ---
        # Variables are key-value pairs extracted or set during the call.
        # These come from the agent's prompt (e.g., collecting a name or email)
        # or from custom tool calls during the call.
        variables = payload.get("variables", {})
        if variables:
            print()
            print("  Variables:")
            for key, value in variables.items():
                print("    {}: {}".format(key, value))

        # --- Metadata ---
        # Custom metadata that was attached to the call when it was created.
        metadata = payload.get("metadata", {})
        if metadata:
            print()
            print("  Metadata:")
            for key, value in metadata.items():
                print("    {}: {}".format(key, value))

        # --- Pathway Logs ---
        # If the call used a pathway, pathway_logs contain the execution trace
        # showing which nodes were visited and what happened at each step.
        pathway_logs = payload.get("pathway_logs", [])
        if pathway_logs:
            print()
            print("  Pathway Logs: {} entries".format(len(pathway_logs)))
            # Show the first 3 log entries as a preview.
            for i, log_entry in enumerate(pathway_logs[:3]):
                print("    [{}] {}".format(i, json.dumps(log_entry)[:200]))
            if len(pathway_logs) > 3:
                print("    ... and {} more entries.".format(len(pathway_logs) - 3))

        # Save the complete payload to the in-memory store.
        save_call_data(call_id, payload)

    print()
    print("=" * 60)
    print()

    # Return a 200 OK response so Bland knows the webhook was received.
    # If you return a non-2xx status, Bland may retry the webhook.
    return jsonify({"status": "received", "call_id": call_id}), 200


# ---------------------------------------------------------------------------
# Health check endpoint: GET /
# ---------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def health_check():
    """
    Simple health check endpoint. Useful for verifying the server is running
    and for load balancer health checks in production.
    """
    return jsonify({
        "status": "ok",
        "message": "Bland AI Webhook Listener is running.",
        "calls_received": len(call_store),
    }), 200


# ---------------------------------------------------------------------------
# List received calls: GET /calls
# ---------------------------------------------------------------------------

@app.route("/calls", methods=["GET"])
def list_received_calls():
    """
    Returns a list of all call_ids that have been received via webhooks.
    Useful for debugging and verifying that webhooks are arriving.
    """
    call_summaries = []
    for cid, data in call_store.items():
        call_summaries.append({
            "call_id": cid,
            "completed": data.get("completed"),
            "call_length": data.get("call_length"),
            "summary": (data.get("summary", "") or "")[:100],
            "has_corrected_transcript": "corrected_transcript" in data,
        })

    return jsonify({
        "total": len(call_summaries),
        "calls": call_summaries,
    }), 200


# ---------------------------------------------------------------------------
# Run the server
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("Bland AI Webhook Listener")
    print("=" * 60)
    print()
    print("Listening on port {}".format(PORT))
    print()
    print("Endpoints:")
    print("  GET  /                        Health check")
    print("  GET  /calls                   List received calls")
    print("  POST /webhook/call-complete   Receive post-call webhooks")
    print()
    print("To receive webhooks from Bland AI:")
    print("  1. Expose this server to the internet (e.g., ngrok http {})".format(PORT))
    print("  2. Set the webhook URL when creating a call:")
    print('     "webhook": "https://your-url/webhook/call-complete"')
    print()
    print("Press Ctrl+C to stop the server.")
    print()

    # Run the Flask development server.
    # In production, use a proper WSGI server like Gunicorn:
    #   gunicorn webhook_listener:app -b 0.0.0.0:3000
    app.run(
        host="0.0.0.0",   # Listen on all interfaces so ngrok can reach it
        port=PORT,
        debug=True,        # Enable auto-reload and detailed error pages
    )
