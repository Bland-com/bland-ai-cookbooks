"""
Bland AI - Analyze a Call (Python)

This script fetches the details of a specific call and then runs AI-powered
analysis on the transcript. It asks practical questions about the call and
displays the structured answers.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run with a specific call ID:
           python analyze_call.py <call_id>
       Or run without arguments to analyze your most recent call:
           python analyze_call.py

The script will:
    - Fetch the call details and display basic metadata
    - Send the call transcript to the AI analysis endpoint
    - Display the analysis results in a readable format
"""

import os
import sys
import json

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
# This keeps your API key out of source control.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
# The key is sent in the Authorization header of every request.
API_KEY = os.getenv("BLAND_API_KEY")

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
# Determine the call ID to analyze
# ---------------------------------------------------------------------------

# The call_id can be passed as a command-line argument.
# If no argument is provided, the script fetches the most recent call.
call_id = None

if len(sys.argv) >= 2:
    # Use the call_id provided on the command line.
    call_id = sys.argv[1]
else:
    # No call_id provided. Fetch the most recent call from the list endpoint.
    print("No call_id provided. Fetching your most recent call...")
    print()

    try:
        # GET /v1/calls returns an array of recent calls.
        # We grab the first one (most recent) and use its call_id.
        list_response = requests.get(
            "{}/calls".format(BASE_URL),
            headers={"Authorization": API_KEY},
            timeout=15,
        )
        list_response.raise_for_status()

        # The response is a JSON array of call objects.
        calls = list_response.json()

        # Handle the case where the response is wrapped in an object.
        # Some API versions return { "calls": [...] } instead of a bare array.
        if isinstance(calls, dict):
            calls = calls.get("calls", [])

        if not calls:
            print("No calls found on your account.")
            print("Send a test call first using the getting-started cookbook.")
            sys.exit(1)

        # Use the first call in the list (most recent).
        call_id = calls[0].get("call_id")
        print("Using most recent call: {}".format(call_id))
        print()

    except requests.exceptions.RequestException as e:
        print("Error fetching call list: {}".format(e))
        sys.exit(1)

# ---------------------------------------------------------------------------
# Fetch call details
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print("Fetching details for call: {}".format(call_id))
print()

try:
    # GET /v1/calls/{call_id} returns the full details for a single call.
    # This includes the transcript, summary, duration, cost, variables, and more.
    response = requests.get(
        "{}/calls/{}".format(BASE_URL, call_id),
        headers=headers,
        timeout=15,
    )
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

# Parse the JSON response containing all call details.
call_data = response.json()

# ---------------------------------------------------------------------------
# Display basic call information
# ---------------------------------------------------------------------------

print("=" * 60)
print("CALL DETAILS")
print("=" * 60)
print()

# Basic metadata about the call.
print("Call ID:       {}".format(call_data.get("call_id", "N/A")))
print("Status:        {}".format(call_data.get("status", "N/A")))
print("Completed:     {}".format(call_data.get("completed", "N/A")))
print()

# Phone numbers and direction.
print("To:            {}".format(call_data.get("to", "N/A")))
print("From:          {}".format(call_data.get("from", "N/A")))
print("Inbound:       {}".format(call_data.get("inbound", "N/A")))
print("Answered By:   {}".format(call_data.get("answered_by", "N/A")))
print("Ended By:      {}".format(call_data.get("call_ended_by", "N/A")))
print()

# Duration and cost.
call_length = call_data.get("call_length")
if call_length is not None:
    print("Duration:      {:.1f} minutes".format(call_length))
else:
    print("Duration:      N/A")

price = call_data.get("price")
if price is not None:
    print("Cost:          ${:.4f}".format(price))
else:
    print("Cost:          N/A")

print()

# Show the recording URL if the call was recorded.
recording_url = call_data.get("recording_url")
if recording_url:
    print("Recording:     {}".format(recording_url))
    print()

# Show the AI-generated summary if available.
summary = call_data.get("summary", "")
if summary:
    print("Summary:")
    print("  {}".format(summary))
    print()

# Show any extracted variables from the call.
variables = call_data.get("variables", {})
if variables:
    print("Variables:")
    for key, value in variables.items():
        print("  {}: {}".format(key, value))
    print()

# Show the transcript preview (first few lines).
concatenated = call_data.get("concatenated_transcript", "")
if concatenated:
    print("Transcript Preview:")
    # Show the first 500 characters of the transcript as a preview.
    preview = concatenated[:500]
    if len(concatenated) > 500:
        preview += "..."
    print("  {}".format(preview))
    print()

# ---------------------------------------------------------------------------
# Run AI analysis on the call
# ---------------------------------------------------------------------------

# The analysis endpoint lets you ask natural-language questions about a call
# and get structured, typed answers back. Each question is a two-element
# array: [question_text, expected_answer_type].
#
# Supported answer types:
#   "string"   - Returns a free-text answer.
#   "boolean"  - Returns true or false.
#   "number"   - Returns a numeric value.
#   Custom     - Returns one of the values in the string (e.g., "human or voicemail").
#
# If a question cannot be answered from the transcript, the answer is null.

print("=" * 60)
print("AI ANALYSIS")
print("=" * 60)
print()
print("Running AI analysis on the call transcript...")
print()

# Define the analysis request.
# The "goal" gives the AI context about what you are trying to evaluate.
# The "questions" array contains the specific questions to answer.
analysis_payload = {
    # The goal provides high-level context for the analysis.
    # It helps the AI understand the purpose of your questions so it can
    # give more relevant and accurate answers.
    "goal": (
        "Evaluate the quality and outcome of this phone call. "
        "Determine customer sentiment, whether key objectives were met, "
        "and extract any important details from the conversation."
    ),

    # Each question is a two-element array: [question_text, answer_type].
    # The answer_type tells the AI what format to return.
    "questions": [
        # Boolean question: returns true or false.
        # Useful for yes/no determinations about the call.
        ["Did the customer express interest in the product?", "boolean"],

        # String question: returns a free-text answer.
        # Good for extracting specific details or open-ended insights.
        ["What was the customer's main concern?", "string"],

        # Boolean question: checks whether an objective was achieved.
        ["Was the issue resolved?", "boolean"],

        # Number question: returns a numeric score.
        # The AI infers the number from the conversation tone and content.
        ["On a scale of 1 to 10, how satisfied did the customer seem?", "number"],

        # Custom answer type: returns one of the specified values.
        # Useful when you want the answer constrained to specific options.
        ["Was the call answered by a human or voicemail?", "human or voicemail"],
    ],
}

try:
    # POST /v1/calls/{call_id}/analyze sends the questions to the AI and
    # returns structured answers based on the call transcript.
    analysis_response = requests.post(
        "{}/calls/{}/analyze".format(BASE_URL, call_id),
        json=analysis_payload,
        headers=headers,
        timeout=30,  # Analysis can take a few seconds for long transcripts
    )
    analysis_response.raise_for_status()

except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the Bland API for analysis.")
    sys.exit(1)

except requests.exceptions.Timeout:
    print("Error: The analysis request timed out.")
    print("This can happen with very long transcripts. Try again.")
    sys.exit(1)

except requests.exceptions.HTTPError:
    print("Error: Analysis API returned status code {}.".format(
        analysis_response.status_code
    ))
    print("Response: {}".format(analysis_response.text))
    sys.exit(1)

# Parse the analysis response.
analysis_data = analysis_response.json()

# ---------------------------------------------------------------------------
# Display analysis results
# ---------------------------------------------------------------------------

# Check if the analysis was successful.
if analysis_data.get("status") == "success":
    # The "answers" array corresponds to the "questions" array by index.
    # answers[0] is the answer to questions[0], answers[1] to questions[1], etc.
    answers = analysis_data.get("answers", [])

    # The questions we asked, for display purposes.
    questions = analysis_payload["questions"]

    # Print each question with its answer in a readable format.
    for i, question_pair in enumerate(questions):
        question_text = question_pair[0]    # The question string
        answer_type = question_pair[1]      # The expected answer type

        # Get the corresponding answer, defaulting to "N/A" if missing.
        answer = answers[i] if i < len(answers) else "N/A"

        # Format null answers as a readable string.
        if answer is None:
            answer = "(could not be determined from transcript)"

        # Format boolean answers for readability.
        if isinstance(answer, bool):
            answer = "Yes" if answer else "No"

        print("Q: {}".format(question_text))
        print("   Type: {}".format(answer_type))
        print("   A: {}".format(answer))
        print()

    # Show the credits used for this analysis.
    # Base cost: 0.003 credits, plus 0.0015 per call, adjusted for length.
    credits_used = analysis_data.get("credits_used", 0)
    print("Credits used for analysis: {}".format(credits_used))
    print()

else:
    # The analysis failed or returned an unexpected status.
    print("Analysis was not successful.")
    print("Response:")
    print(json.dumps(analysis_data, indent=2))
    print()

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

print("=" * 60)
print("Done.")
