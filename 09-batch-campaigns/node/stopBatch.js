/**
 * Bland AI - Stop a Batch Campaign (Node.js)
 *
 * This script stops a running batch campaign. Calls that are already in progress
 * will finish naturally, but no new calls will be dispatched.
 *
 * This is useful when you need to:
 * - Halt a campaign due to an error in the prompt
 * - Stop a batch that was accidentally started with wrong data
 * - Cancel a campaign that is no longer needed
 *
 * Usage:
 *     1. Copy .env.example to .env and fill in your API key.
 *     2. Install dependencies: npm install axios dotenv
 *     3. Run: node stopBatch.js <batch_id>
 *
 * The script will:
 *     - Ask for confirmation before stopping
 *     - Send a stop request to POST /v1/batches/{batch_id}/stop
 *     - Print the result (success or error)
 *     - Fetch and display the final batch status
 */

const readline = require("readline");
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
  console.log("Usage: node stopBatch.js <batch_id>");
  console.log();
  console.log("Example:");
  console.log("  node stopBatch.js xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx");
  console.log();
  console.log("You can get the batch_id from the output of createBatch.js,");
  console.log("or from the Bland dashboard at https://app.bland.ai");
  process.exit(1);
}

const batchId = process.argv[2];

// ---------------------------------------------------------------------------
// Set up the HTTP headers
// ---------------------------------------------------------------------------

// Bland uses a simple API key in the Authorization header (no "Bearer" prefix).
const headers = {
  Authorization: API_KEY,
  "Content-Type": "application/json",
};

// ---------------------------------------------------------------------------
// Helper: prompt the user for confirmation
// ---------------------------------------------------------------------------

/**
 * Prompts the user for input on the command line and returns their answer.
 *
 * @param {string} question - The question to display.
 * @returns {Promise<string>} The user's input, trimmed and lowercased.
 */
function askQuestion(question) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise((resolve) => {
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim().toLowerCase());
    });
  });
}

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

/**
 * Confirms the stop action, sends the stop request, and displays the result.
 */
async function stopBatch() {
  // -----------------------------------------------------------------
  // Confirm the stop action
  // -----------------------------------------------------------------

  // Stopping a batch is a significant action, so we ask for confirmation.
  // This is especially important if you have a large campaign running.
  console.log("You are about to stop batch: " + batchId);
  console.log();
  console.log("Important:");
  console.log("  - Calls already in progress will finish normally.");
  console.log("  - No new calls will be dispatched after stopping.");
  console.log("  - This action cannot be undone.");
  console.log();

  const confirmation = await askQuestion("Type 'stop' to confirm: ");

  if (confirmation !== "stop") {
    console.log("Cancelled. The batch was not stopped.");
    process.exit(0);
  }

  // -----------------------------------------------------------------
  // Send the stop request
  // -----------------------------------------------------------------

  console.log();
  console.log("Stopping batch " + batchId + "...");

  try {
    // Make the POST request to the Stop Batch endpoint.
    const response = await axios.post(
      BASE_URL + "/batches/" + batchId + "/stop",
      {},
      {
        headers,
        timeout: 30000,
      }
    );

    const data = response.data;

    console.log();
    console.log("Batch stop request sent successfully.");
    console.log();
    console.log("Response:");
    console.log("  " + JSON.stringify(data));
    console.log();
  } catch (error) {
    if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API.");
      console.error("Check your internet connection and try again.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The request timed out.");
      console.error("The Bland API may be experiencing high traffic. Try again in a moment.");
    } else if (error.response) {
      console.error("Error: API returned status code " + error.response.status + ".");
      console.error("Response: " + JSON.stringify(error.response.data));
    } else {
      console.error("Error: " + error.message);
    }
    process.exit(1);
  }

  // -----------------------------------------------------------------
  // Fetch the final batch status for confirmation
  // -----------------------------------------------------------------

  console.log("Fetching current batch status...");
  console.log();

  try {
    const statusResponse = await axios.get(
      BASE_URL + "/batches/" + batchId,
      {
        headers,
        timeout: 15000,
      }
    );

    const statusData = statusResponse.data;
    const status = statusData.status || "unknown";
    const totalCalls = statusData.calls_total || statusData.total_calls || 0;
    const successfulCalls = statusData.calls_successful || statusData.successful_calls || 0;
    const failedCalls = statusData.calls_failed || statusData.failed_calls || 0;

    console.log("=".repeat(40));
    console.log("  BATCH STATUS AFTER STOP");
    console.log("=".repeat(40));
    console.log("  Batch ID:    " + batchId);
    console.log("  Status:      " + status);
    console.log("  Total Calls: " + totalCalls);
    console.log("  Successful:  " + successfulCalls);
    console.log("  Failed:      " + failedCalls);
    console.log("=".repeat(40));
    console.log();
    console.log("Note: Calls that were already in progress may still be running.");
    console.log("Check the Bland dashboard for the final results.");
  } catch (err) {
    // If we cannot fetch the status, just let the user know.
    // The stop request already succeeded, so this is not critical.
    console.log("Could not fetch updated batch status: " + err.message);
    console.log("The stop request was sent successfully.");
    console.log("Check the Bland dashboard for current status.");
  }
}

// Run the main function.
stopBatch();
