/**
 * Bland AI - Monitor a Batch Campaign (Node.js)
 *
 * This script polls the Bland AI API to track the progress of a running batch
 * campaign. It displays real-time status updates including how many calls have
 * completed, how many are still in progress, and how many have failed.
 *
 * Usage:
 *     1. Copy .env.example to .env and fill in your API key.
 *     2. Install dependencies: npm install axios dotenv
 *     3. Run: node monitorBatch.js <batch_id>
 *
 * The script will:
 *     - Poll GET /v1/batches/{batch_id} every 10 seconds
 *     - Display the current batch status and call counts
 *     - Exit automatically when the batch reaches a terminal status
 *     - Show a final summary with total calls, successes, and failures
 *
 * You can press Ctrl+C at any time to stop monitoring without affecting the batch.
 * The batch will continue running regardless of whether this script is active.
 */

const axios = require("axios");

// Load environment variables from the .env file in this directory.
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key.
const API_KEY = process.env.BLAND_API_KEY;

// The Bland API base URL.
const BASE_URL = "https://api.bland.ai/v1";

// How often to poll the API, in seconds. 10 seconds is a good balance between
// responsiveness and avoiding excessive API calls. For very large batches
// (1000+ calls), you might increase this to 30 seconds.
const POLL_INTERVAL = 10;

// Maximum time to poll before giving up, in seconds. Set to 0 for no limit.
// 1 hour is a reasonable timeout for most batch sizes.
const MAX_POLL_TIME = 3600;

// Terminal statuses that indicate the batch has finished processing.
// When the batch reaches one of these statuses, the script exits.
const TERMINAL_STATUSES = new Set(["completed", "completed_partial", "failed"]);

// ---------------------------------------------------------------------------
// Validate configuration
// ---------------------------------------------------------------------------

if (!API_KEY) {
  console.error("Error: BLAND_API_KEY is not set.");
  console.error("Copy .env.example to .env and add your API key.");
  process.exit(1);
}

// The batch_id should be passed as a command-line argument.
// process.argv[0] is "node", process.argv[1] is the script path,
// so the batch_id is process.argv[2].
if (process.argv.length < 3) {
  console.log("Usage: node monitorBatch.js <batch_id>");
  console.log();
  console.log("Example:");
  console.log("  node monitorBatch.js xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx");
  console.log();
  console.log("You can get the batch_id by running createBatch.js first.");
  process.exit(1);
}

const batchId = process.argv[2];

// ---------------------------------------------------------------------------
// Set up the HTTP headers
// ---------------------------------------------------------------------------

// Bland uses a simple API key in the Authorization header (no "Bearer" prefix).
const headers = {
  Authorization: API_KEY,
};

// ---------------------------------------------------------------------------
// Helper: sleep for a given number of milliseconds
// ---------------------------------------------------------------------------

/**
 * Returns a promise that resolves after the specified number of milliseconds.
 * Used to wait between poll intervals.
 *
 * @param {number} ms - The number of milliseconds to sleep.
 * @returns {Promise<void>}
 */
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Helper: format the current time as HH:MM:SS
// ---------------------------------------------------------------------------

/**
 * Returns the current local time formatted as HH:MM:SS.
 * Used for timestamps in the polling output.
 *
 * @returns {string} Formatted time string.
 */
function timestamp() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const ss = String(now.getSeconds()).padStart(2, "0");
  return hh + ":" + mm + ":" + ss;
}

// ---------------------------------------------------------------------------
// Helper: build a simple progress bar string
// ---------------------------------------------------------------------------

/**
 * Builds an ASCII progress bar for display.
 *
 * @param {number} completed - The number of completed items.
 * @param {number} total - The total number of items.
 * @param {number} width - The width of the progress bar in characters.
 * @returns {string} A progress bar string like "[######------] 50.0%"
 */
function progressBar(completed, total, width) {
  if (total === 0) return "[" + "-".repeat(width) + "]   0.0%";
  const pct = completed / total;
  const filled = Math.round(width * pct);
  const empty = width - filled;
  const bar = "#".repeat(filled) + "-".repeat(empty);
  return "[" + bar + "] " + (pct * 100).toFixed(1) + "%";
}

// ---------------------------------------------------------------------------
// Poll the batch status
// ---------------------------------------------------------------------------

/**
 * Main polling loop. Fetches the batch status on each iteration,
 * displays progress, and exits when the batch reaches a terminal state
 * or the maximum poll time is exceeded.
 */
async function monitorBatch() {
  console.log("Monitoring batch: " + batchId);
  console.log("Polling every " + POLL_INTERVAL + " seconds. Press Ctrl+C to stop.");
  console.log();
  console.log("-".repeat(70));

  let elapsed = 0;

  while (true) {
    // Check if we have exceeded the maximum poll time.
    if (MAX_POLL_TIME > 0 && elapsed >= MAX_POLL_TIME) {
      console.log();
      console.log("Polling timed out after " + MAX_POLL_TIME + " seconds.");
      console.log("The batch may still be running. Check the Bland dashboard or");
      console.log("run this script again to continue monitoring.");
      break;
    }

    // -----------------------------------------------------------------
    // Fetch the current batch status
    // -----------------------------------------------------------------

    let data;

    try {
      const response = await axios.get(BASE_URL + "/batches/" + batchId, {
        headers,
        timeout: 15000,
      });
      data = response.data;
    } catch (error) {
      if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
        console.log("  [Warning] Connection error. Retrying in " + POLL_INTERVAL + " seconds...");
      } else if (error.code === "ECONNABORTED") {
        console.log("  [Warning] Request timed out. Retrying in " + POLL_INTERVAL + " seconds...");
      } else if (error.response) {
        console.error("Error: API returned status code " + error.response.status + ".");
        console.error("Response: " + JSON.stringify(error.response.data));
        process.exit(1);
      } else {
        console.error("Error: " + error.message);
        process.exit(1);
      }

      // Wait before retrying.
      await sleep(POLL_INTERVAL * 1000);
      elapsed += POLL_INTERVAL;
      continue;
    }

    // -----------------------------------------------------------------
    // Extract and display batch information
    // -----------------------------------------------------------------

    // The batch status tracks the overall lifecycle of the campaign.
    // Possible values:
    //   validating                 - Bland is checking the batch configuration
    //   dispatching                - Calls are being queued and sent
    //   in_progress                - Calls are actively running
    //   in_progress_chunked        - Large batch being processed in chunks
    //   waiting_for_scheduled_calls - Immediate calls done, waiting for scheduled ones
    //   completed                  - All calls finished successfully
    //   completed_partial          - Batch finished but some calls failed
    //   failed                     - The batch failed entirely
    const status = data.status || "unknown";

    // Extract call counts. These fields may not be present in every
    // response, especially during early stages like "validating".
    const totalCalls = data.calls_total || data.total_calls || 0;
    const successfulCalls = data.calls_successful || data.successful_calls || 0;
    const failedCalls = data.calls_failed || data.failed_calls || 0;
    const inProgressCalls = data.calls_in_progress || data.in_progress_calls || 0;

    // Calculate completed calls (successful + failed).
    const completedCalls = successfulCalls + failedCalls;

    // Build the progress display.
    const ts = timestamp();

    if (totalCalls > 0) {
      // Show a progress bar when we know the total.
      const bar = progressBar(completedCalls, totalCalls, 30);
      const statusPadded = status.padEnd(28);
      console.log("  [" + ts + "]  Status: " + statusPadded + "  " + bar);
      console.log(
        "           Total: " + totalCalls +
        "  |  Successful: " + successfulCalls +
        "  |  In Progress: " + inProgressCalls +
        "  |  Failed: " + failedCalls
      );
    } else {
      // If we do not have call counts yet, just show the status.
      console.log("  [" + ts + "]  Status: " + status);
    }

    console.log("-".repeat(70));

    // -----------------------------------------------------------------
    // Check for terminal status
    // -----------------------------------------------------------------

    if (TERMINAL_STATUSES.has(status)) {
      console.log();
      console.log("Batch has reached terminal status: " + status);
      console.log();

      // Print a final summary.
      console.log("=".repeat(40));
      console.log("  BATCH SUMMARY");
      console.log("=".repeat(40));
      console.log("  Batch ID:    " + batchId);
      console.log("  Status:      " + status);
      console.log("  Total Calls: " + totalCalls);
      console.log("  Successful:  " + successfulCalls);
      console.log("  Failed:      " + failedCalls);
      console.log("=".repeat(40));

      if (status === "completed") {
        console.log();
        console.log("All calls completed successfully.");
      } else if (status === "completed_partial") {
        console.log();
        console.log("The batch completed but " + failedCalls + " call(s) failed.");
        console.log("Check individual call details for error messages.");
      } else if (status === "failed") {
        console.log();
        console.log("The batch failed. Check the Bland dashboard for details.");
      }

      console.log();
      console.log("To review individual call transcripts and recordings,");
      console.log("visit the Bland dashboard at https://app.bland.ai");
      break;
    }

    // -----------------------------------------------------------------
    // Wait before the next poll
    // -----------------------------------------------------------------

    await sleep(POLL_INTERVAL * 1000);
    elapsed += POLL_INTERVAL;
  }
}

// Handle Ctrl+C gracefully. The batch continues running regardless.
process.on("SIGINT", () => {
  console.log();
  console.log();
  console.log("Monitoring stopped. The batch is still running.");
  console.log("Run this script again to resume monitoring:");
  console.log("  node monitorBatch.js " + batchId);
  process.exit(0);
});

// Run the main function.
monitorBatch();
