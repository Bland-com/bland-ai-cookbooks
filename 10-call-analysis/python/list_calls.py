"""
Bland AI - List Recent Calls (Python)

This script fetches your recent calls from the Bland AI API and displays
them in a formatted table. It shows the call ID, phone numbers, duration,
status, and a truncated summary for each call.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python list_calls.py

The script will:
    - Fetch all recent calls from your account
    - Display them in a formatted table
    - Show key metadata for each call at a glance
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

# The Bland API base URL. All endpoints are under this path.
BASE_URL = "https://api.bland.ai/v1"

# Maximum width for the summary column in the output table.
# Summaries longer than this will be truncated with "..." appended.
SUMMARY_MAX_WIDTH = 50

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Fetch recent calls
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
}

print("Fetching recent calls...")
print()

try:
    # GET /v1/calls returns an array of your recent calls.
    # Each call object includes all details: call_id, to, from, duration,
    # status, summary, transcript, variables, and more.
    response = requests.get(
        "{}/calls".format(BASE_URL),
        headers=headers,
        timeout=15,
    )

    # Raise an exception for HTTP error codes (4xx, 5xx).
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
    if response.status_code == 401:
        print("Invalid API key. Check your .env file.")
    else:
        print("Response: {}".format(response.text))
    sys.exit(1)

# Parse the JSON response.
data = response.json()

# The response may be a bare array of calls, or an object wrapping them.
# Handle both cases so the script works regardless of API version.
if isinstance(data, dict):
    calls = data.get("calls", [])
elif isinstance(data, list):
    calls = data
else:
    print("Unexpected response format.")
    print("Response: {}".format(data))
    sys.exit(1)

# ---------------------------------------------------------------------------
# Display calls in a formatted table
# ---------------------------------------------------------------------------

if not calls:
    print("No calls found on your account.")
    print("Send a test call first using the getting-started cookbook.")
    sys.exit(0)

print("Found {} call(s).".format(len(calls)))
print()

# Define column headers and widths for the output table.
# These widths are chosen to fit common terminal widths (120+ columns).
col_call_id = 38      # UUID format: 36 chars + padding
col_to = 16           # E.164 phone numbers: up to 15 digits + "+"
col_from = 16         # Same as "to"
col_duration = 10     # "12.3 min" format
col_status = 12       # "completed", "in-progress", etc.
col_summary = SUMMARY_MAX_WIDTH  # Truncated summary text

# Print the table header.
header = "{:<{}}  {:<{}}  {:<{}}  {:<{}}  {:<{}}  {}".format(
    "CALL ID", col_call_id,
    "TO", col_to,
    "FROM", col_from,
    "DURATION", col_duration,
    "STATUS", col_status,
    "SUMMARY",
)
print(header)

# Print a separator line under the header.
separator = "{} {} {} {} {} {}".format(
    "-" * col_call_id,
    "-" * col_to,
    "-" * col_from,
    "-" * col_duration,
    "-" * col_status,
    "-" * col_summary,
)
print(separator)

# Print each call as a row in the table.
for call in calls:
    # Extract fields from the call object, with sensible defaults.
    cid = call.get("call_id", "N/A")

    # Phone numbers. These are in E.164 format (e.g., +15551234567).
    to_number = call.get("to", "N/A")
    from_number = call.get("from", "N/A")

    # Call duration in minutes. Format to one decimal place.
    call_length = call.get("call_length")
    if call_length is not None:
        duration_str = "{:.1f} min".format(call_length)
    else:
        duration_str = "N/A"

    # Call status (e.g., "completed", "in-progress", "queued").
    status = call.get("status", "N/A")

    # AI-generated summary. Truncate if it exceeds the column width.
    summary = call.get("summary", "") or ""
    # Remove newlines from the summary so it fits in a single table row.
    summary = summary.replace("\n", " ").strip()
    if len(summary) > SUMMARY_MAX_WIDTH:
        summary = summary[:SUMMARY_MAX_WIDTH - 3] + "..."

    # Print the formatted row.
    row = "{:<{}}  {:<{}}  {:<{}}  {:<{}}  {:<{}}  {}".format(
        cid, col_call_id,
        to_number, col_to,
        from_number, col_from,
        duration_str, col_duration,
        status, col_status,
        summary,
    )
    print(row)

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

print()
print("-" * 80)
print()

# Calculate some basic statistics across all calls.
total_calls = len(calls)

# Count completed calls.
completed_calls = sum(1 for c in calls if c.get("completed"))

# Calculate total duration across all calls.
total_duration = sum(
    c.get("call_length", 0) or 0
    for c in calls
)

# Calculate total cost across all calls.
total_cost = sum(
    c.get("price", 0) or 0
    for c in calls
)

# Count inbound vs outbound calls.
inbound_count = sum(1 for c in calls if c.get("inbound"))
outbound_count = total_calls - inbound_count

print("Total calls:     {}".format(total_calls))
print("Completed:       {}".format(completed_calls))
print("Inbound:         {}".format(inbound_count))
print("Outbound:        {}".format(outbound_count))
print("Total duration:  {:.1f} minutes".format(total_duration))
print("Total cost:      ${:.4f}".format(total_cost))
print()
print("Done.")
