/**
 * Bland AI - List Recent Calls (Node.js)
 *
 * This script fetches your recent calls from the Bland AI API and displays
 * them in a formatted table. It shows the call ID, phone numbers, duration,
 * status, and a truncated summary for each call.
 *
 * Usage:
 *     1. Copy .env.example to .env and fill in your API key.
 *     2. Install dependencies: npm install axios dotenv
 *     3. Run: node listCalls.js
 *
 * The script will:
 *     - Fetch all recent calls from your account
 *     - Display them in a formatted table
 *     - Show key metadata for each call at a glance
 *     - Print summary statistics at the end
 */

const axios = require("axios");

// Load environment variables from the .env file in this directory.
// This keeps your API key out of source control.
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

// The Bland API base URL. All endpoints are under this path.
const BASE_URL = "https://api.bland.ai/v1";

// Maximum width for the summary column in the output table.
// Summaries longer than this will be truncated with "..." appended.
const SUMMARY_MAX_WIDTH = 50;

// ---------------------------------------------------------------------------
// Validate configuration
// ---------------------------------------------------------------------------

if (!API_KEY) {
  console.error("Error: BLAND_API_KEY is not set.");
  console.error("Copy .env.example to .env and add your API key.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Set up the HTTP headers
// ---------------------------------------------------------------------------

// Bland uses a simple API key in the Authorization header (no "Bearer" prefix).
const headers = {
  Authorization: API_KEY,
};

// ---------------------------------------------------------------------------
// Helper: pad a string to a fixed width
// ---------------------------------------------------------------------------

/**
 * Pads a string with spaces on the right to reach the desired width.
 * If the string is longer than the width, it is truncated.
 *
 * @param {string} str - The string to pad.
 * @param {number} width - The desired total width.
 * @returns {string} The padded (or truncated) string.
 */
function padRight(str, width) {
  const s = String(str);
  if (s.length >= width) return s.substring(0, width);
  return s + " ".repeat(width - s.length);
}

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

/**
 * Fetches recent calls from the Bland AI API and displays them
 * in a formatted table with summary statistics.
 */
async function listCalls() {
  console.log("Fetching recent calls...");
  console.log();

  let calls;

  try {
    // GET /v1/calls returns an array of your recent calls.
    // Each call object includes all details: call_id, to, from, duration,
    // status, summary, transcript, variables, and more.
    const response = await axios.get(BASE_URL + "/calls", {
      headers,
      timeout: 15000,
    });

    // The response may be a bare array of calls, or an object wrapping them.
    // Handle both cases so the script works regardless of API version.
    const data = response.data;
    if (Array.isArray(data)) {
      calls = data;
    } else if (typeof data === "object" && data !== null) {
      calls = data.calls || [];
    } else {
      console.error("Unexpected response format.");
      console.error("Response: " + JSON.stringify(data));
      process.exit(1);
    }
  } catch (error) {
    if (error.response) {
      console.error("Error: API returned status code " + error.response.status + ".");
      if (error.response.status === 401) {
        console.error("Invalid API key. Check your .env file.");
      } else {
        console.error("Response: " + JSON.stringify(error.response.data));
      }
    } else if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API.");
      console.error("Check your internet connection and try again.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The request timed out. Try again in a moment.");
    } else {
      console.error("Error: " + error.message);
    }
    process.exit(1);
  }

  // -------------------------------------------------------------------
  // Display calls in a formatted table
  // -------------------------------------------------------------------

  if (!calls || calls.length === 0) {
    console.log("No calls found on your account.");
    console.log("Send a test call first using the getting-started cookbook.");
    process.exit(0);
  }

  console.log("Found " + calls.length + " call(s).");
  console.log();

  // Define column widths for the output table.
  // These widths are chosen to fit common terminal widths (120+ columns).
  const colCallId = 38;    // UUID format: 36 chars + padding
  const colTo = 16;        // E.164 phone numbers: up to 15 digits + "+"
  const colFrom = 16;      // Same as "to"
  const colDuration = 10;  // "12.3 min" format
  const colStatus = 12;    // "completed", "in-progress", etc.

  // Print the table header.
  const headerLine =
    padRight("CALL ID", colCallId) + "  " +
    padRight("TO", colTo) + "  " +
    padRight("FROM", colFrom) + "  " +
    padRight("DURATION", colDuration) + "  " +
    padRight("STATUS", colStatus) + "  " +
    "SUMMARY";
  console.log(headerLine);

  // Print a separator line under the header.
  const separator =
    "-".repeat(colCallId) + " " +
    "-".repeat(colTo) + " " +
    "-".repeat(colFrom) + " " +
    "-".repeat(colDuration) + " " +
    "-".repeat(colStatus) + " " +
    "-".repeat(SUMMARY_MAX_WIDTH);
  console.log(separator);

  // Print each call as a row in the table.
  for (const call of calls) {
    // Extract fields from the call object, with sensible defaults.
    const cid = call.call_id || "N/A";

    // Phone numbers in E.164 format (e.g., +15551234567).
    const toNumber = call.to || "N/A";
    const fromNumber = call.from || "N/A";

    // Call duration in minutes. Format to one decimal place.
    let durationStr = "N/A";
    if (call.call_length != null) {
      durationStr = call.call_length.toFixed(1) + " min";
    }

    // Call status (e.g., "completed", "in-progress", "queued").
    const status = call.status || "N/A";

    // AI-generated summary. Truncate if it exceeds the column width.
    let summary = (call.summary || "").replace(/\n/g, " ").trim();
    if (summary.length > SUMMARY_MAX_WIDTH) {
      summary = summary.substring(0, SUMMARY_MAX_WIDTH - 3) + "...";
    }

    // Print the formatted row.
    const row =
      padRight(cid, colCallId) + "  " +
      padRight(toNumber, colTo) + "  " +
      padRight(fromNumber, colFrom) + "  " +
      padRight(durationStr, colDuration) + "  " +
      padRight(status, colStatus) + "  " +
      summary;
    console.log(row);
  }

  // -------------------------------------------------------------------
  // Summary statistics
  // -------------------------------------------------------------------

  console.log();
  console.log("-".repeat(80));
  console.log();

  // Calculate some basic statistics across all calls.
  const totalCalls = calls.length;

  // Count completed calls.
  const completedCalls = calls.filter((c) => c.completed).length;

  // Calculate total duration across all calls.
  const totalDuration = calls.reduce((sum, c) => sum + (c.call_length || 0), 0);

  // Calculate total cost across all calls.
  const totalCost = calls.reduce((sum, c) => sum + (c.price || 0), 0);

  // Count inbound vs outbound calls.
  const inboundCount = calls.filter((c) => c.inbound).length;
  const outboundCount = totalCalls - inboundCount;

  console.log("Total calls:     " + totalCalls);
  console.log("Completed:       " + completedCalls);
  console.log("Inbound:         " + inboundCount);
  console.log("Outbound:        " + outboundCount);
  console.log("Total duration:  " + totalDuration.toFixed(1) + " minutes");
  console.log("Total cost:      $" + totalCost.toFixed(4));
  console.log();
  console.log("Done.");
}

// Run the main function.
listCalls();
