"""
Bland AI - Monitor a Batch Campaign (Python)

This script polls the Bland AI API to track the progress of a running batch
campaign. It displays real-time status updates including how many calls have
completed, how many are still in progress, and how many have failed.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python monitor_batch.py <batch_id>

The script will:
    - Poll GET /v1/batches/{batch_id} every 10 seconds
    - Display the current batch status and call counts
    - Exit automatically when the batch reaches a terminal status
    - Show a final summary with total calls, successes, and failures

You can press Ctrl+C at any time to stop monitoring without affecting the batch.
The batch will continue running regardless of whether this script is active.
"""

import os
import sys
import time

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

# How often to poll the API, in seconds. 10 seconds is a good balance between
# responsiveness and avoiding excessive API calls. For very large batches
# (1000+ calls), you might increase this to 30 seconds.
POLL_INTERVAL = 10

# Maximum time to poll before giving up, in seconds. Set to 0 for no limit.
# 1 hour is a reasonable timeout for most batch sizes.
MAX_POLL_TIME = 3600

# Terminal statuses that indicate the batch has finished processing.
# When the batch reaches one of these statuses, the script exits.
TERMINAL_STATUSES = {"completed", "completed_partial", "failed"}

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

# The batch_id should be passed as a command-line argument.
if len(sys.argv) < 2:
    print("Usage: python monitor_batch.py <batch_id>")
    print()
    print("Example:")
    print("  python monitor_batch.py xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
    print()
    print("You can get the batch_id by running create_batch.py first.")
    sys.exit(1)

batch_id = sys.argv[1]

# ---------------------------------------------------------------------------
# Set up the HTTP headers
# ---------------------------------------------------------------------------

# Bland uses a simple API key in the Authorization header (no "Bearer" prefix).
headers = {
    "Authorization": API_KEY,
}

# ---------------------------------------------------------------------------
# Poll the batch status
# ---------------------------------------------------------------------------

print("Monitoring batch: {}".format(batch_id))
print("Polling every {} seconds. Press Ctrl+C to stop.".format(POLL_INTERVAL))
print()
print("-" * 70)

elapsed = 0

try:
    while True:
        # Check if we have exceeded the maximum poll time.
        if MAX_POLL_TIME > 0 and elapsed >= MAX_POLL_TIME:
            print()
            print("Polling timed out after {} seconds.".format(MAX_POLL_TIME))
            print("The batch may still be running. Check the Bland dashboard or")
            print("run this script again to continue monitoring.")
            break

        # -------------------------------------------------------------------
        # Fetch the current batch status
        # -------------------------------------------------------------------

        try:
            response = requests.get(
                "{}/batches/{}".format(BASE_URL, batch_id),
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()

        except requests.exceptions.ConnectionError:
            print("  [Warning] Connection error. Retrying in {} seconds...".format(POLL_INTERVAL))
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            continue

        except requests.exceptions.Timeout:
            print("  [Warning] Request timed out. Retrying in {} seconds...".format(POLL_INTERVAL))
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
            continue

        except requests.exceptions.HTTPError:
            print("Error: API returned status code {}.".format(response.status_code))
            print("Response: {}".format(response.text))
            sys.exit(1)

        # Parse the response.
        data = response.json()

        # -------------------------------------------------------------------
        # Extract and display batch information
        # -------------------------------------------------------------------

        # The batch status tracks the overall lifecycle of the campaign.
        # Possible values:
        #   validating                - Bland is checking the batch configuration
        #   dispatching               - Calls are being queued and sent
        #   in_progress               - Calls are actively running
        #   in_progress_chunked       - Large batch being processed in chunks
        #   waiting_for_scheduled_calls - Immediate calls done, waiting for scheduled ones
        #   completed                 - All calls finished successfully
        #   completed_partial         - Batch finished but some calls failed
        #   failed                    - The batch failed entirely
        status = data.get("status", "unknown")

        # Extract call counts. These fields may not be present in every
        # response, especially during early stages like "validating".
        total_calls = data.get("calls_total", data.get("total_calls", 0))
        successful_calls = data.get("calls_successful", data.get("successful_calls", 0))
        failed_calls = data.get("calls_failed", data.get("failed_calls", 0))
        in_progress_calls = data.get("calls_in_progress", data.get("in_progress_calls", 0))

        # Calculate completed calls (successful + failed).
        completed_calls = successful_calls + failed_calls

        # Build the progress display.
        timestamp = time.strftime("%H:%M:%S")

        if total_calls > 0:
            # Show a progress bar when we know the total.
            progress_pct = (completed_calls / total_calls) * 100
            bar_width = 30
            filled = int(bar_width * completed_calls / total_calls)
            bar = "#" * filled + "-" * (bar_width - filled)

            print(
                "  [{time}]  Status: {status:<28s}  [{bar}] {pct:5.1f}%".format(
                    time=timestamp,
                    status=status,
                    bar=bar,
                    pct=progress_pct,
                )
            )
            print(
                "           Total: {total}  |  Successful: {success}  |  "
                "In Progress: {progress}  |  Failed: {failed}".format(
                    total=total_calls,
                    success=successful_calls,
                    progress=in_progress_calls,
                    failed=failed_calls,
                )
            )
        else:
            # If we do not have call counts yet, just show the status.
            print(
                "  [{time}]  Status: {status}".format(
                    time=timestamp,
                    status=status,
                )
            )

        print("-" * 70)

        # -------------------------------------------------------------------
        # Check for terminal status
        # -------------------------------------------------------------------

        if status in TERMINAL_STATUSES:
            print()
            print("Batch has reached terminal status: {}".format(status))
            print()

            # Print a final summary.
            print("=" * 40)
            print("  BATCH SUMMARY")
            print("=" * 40)
            print("  Batch ID:    {}".format(batch_id))
            print("  Status:      {}".format(status))
            print("  Total Calls: {}".format(total_calls))
            print("  Successful:  {}".format(successful_calls))
            print("  Failed:      {}".format(failed_calls))
            print("=" * 40)

            if status == "completed":
                print()
                print("All calls completed successfully.")
            elif status == "completed_partial":
                print()
                print("The batch completed but {} call(s) failed.".format(failed_calls))
                print("Check individual call details for error messages.")
            elif status == "failed":
                print()
                print("The batch failed. Check the Bland dashboard for details.")

            print()
            print("To review individual call transcripts and recordings,")
            print("visit the Bland dashboard at https://app.bland.ai")
            break

        # -------------------------------------------------------------------
        # Wait before the next poll
        # -------------------------------------------------------------------

        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

except KeyboardInterrupt:
    # The user pressed Ctrl+C. Exit gracefully.
    print()
    print()
    print("Monitoring stopped. The batch is still running.")
    print("Run this script again to resume monitoring:")
    print("  python monitor_batch.py {}".format(batch_id))
    sys.exit(0)
