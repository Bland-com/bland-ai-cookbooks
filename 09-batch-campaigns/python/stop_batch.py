"""
Bland AI - Stop a Batch Campaign (Python)

This script stops a running batch campaign. Calls that are already in progress
will finish naturally, but no new calls will be dispatched.

This is useful when you need to:
- Halt a campaign due to an error in the prompt
- Stop a batch that was accidentally started with wrong data
- Cancel a campaign that is no longer needed

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python stop_batch.py <batch_id>

The script will:
    - Send a stop request to POST /v1/batches/{batch_id}/stop
    - Print the result (success or error)
    - Show the final batch status
"""

import os
import sys

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
load_dotenv()

# Your Bland API key.
API_KEY = os.getenv("BLAND_API_KEY")

# The Bland API base URL.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

# The batch_id should be passed as a command-line argument.
if len(sys.argv) < 2:
    print("Usage: python stop_batch.py <batch_id>")
    print()
    print("Example:")
    print("  python stop_batch.py xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    print()
    print("You can get the batch_id from the output of create_batch.py,")
    print("or from the Bland dashboard at https://app.bland.ai")
    sys.exit(1)

batch_id = sys.argv[1]

# ---------------------------------------------------------------------------
# Confirm the stop action
# ---------------------------------------------------------------------------

# Stopping a batch is a significant action, so we ask for confirmation.
# This is especially important if you have a large campaign running.
print("You are about to stop batch: {}".format(batch_id))
print()
print("Important:")
print("  - Calls already in progress will finish normally.")
print("  - No new calls will be dispatched after stopping.")
print("  - This action cannot be undone.")
print()

confirmation = input("Type 'stop' to confirm: ").strip().lower()

if confirmation != "stop":
    print("Cancelled. The batch was not stopped.")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Send the stop request
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print()
print("Stopping batch {}...".format(batch_id))

try:
    # Make the POST request to the Stop Batch endpoint.
    response = requests.post(
        "{}/batches/{}/stop".format(BASE_URL, batch_id),
        headers=headers,
        timeout=30,
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

data = response.json()

print()
print("Batch stop request sent successfully.")
print()
print("Response:")
print("  {}".format(data))
print()

# ---------------------------------------------------------------------------
# Fetch the final batch status for confirmation
# ---------------------------------------------------------------------------

print("Fetching current batch status...")
print()

try:
    status_response = requests.get(
        "{}/batches/{}".format(BASE_URL, batch_id),
        headers=headers,
        timeout=15,
    )
    status_response.raise_for_status()
    status_data = status_response.json()

    status = status_data.get("status", "unknown")
    total_calls = status_data.get("calls_total", status_data.get("total_calls", 0))
    successful_calls = status_data.get("calls_successful", status_data.get("successful_calls", 0))
    failed_calls = status_data.get("calls_failed", status_data.get("failed_calls", 0))

    print("=" * 40)
    print("  BATCH STATUS AFTER STOP")
    print("=" * 40)
    print("  Batch ID:    {}".format(batch_id))
    print("  Status:      {}".format(status))
    print("  Total Calls: {}".format(total_calls))
    print("  Successful:  {}".format(successful_calls))
    print("  Failed:      {}".format(failed_calls))
    print("=" * 40)
    print()
    print("Note: Calls that were already in progress may still be running.")
    print("Check the Bland dashboard for the final results.")

except Exception as e:
    # If we cannot fetch the status, just let the user know.
    # The stop request already succeeded, so this is not critical.
    print("Could not fetch updated batch status: {}".format(e))
    print("The stop request was sent successfully.")
    print("Check the Bland dashboard for current status.")
