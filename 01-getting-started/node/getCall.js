/**
 * Bland AI - Get Call Details (Node.js)
 *
 * This script retrieves the details of a completed call using the Bland AI API.
 * It prints the transcript, summary, duration, cost, and other metadata.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node getCall.js <call_id>
 *
 * The call_id is printed by sendCall.js when you send a call.
 * You can also find call IDs in the Bland dashboard under the Calls tab.
 */

// Load environment variables from .env file.
require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key.
const API_KEY = process.env.BLAND_API_KEY;

// The Bland API base URL.
const BASE_URL = "https://api.bland.ai/v1";

// ---------------------------------------------------------------------------
// Validate inputs
// ---------------------------------------------------------------------------

if (!API_KEY) {
  console.error("Error: BLAND_API_KEY is not set.");
  console.error("Copy .env.example to .env and add your API key.");
  process.exit(1);
}

// The call_id should be passed as a command-line argument.
// Example: node getCall.js abc12345-def6-7890-ghij-klmnopqrstuv
const callId = process.argv[2];

if (!callId) {
  console.log("Usage: node getCall.js <call_id>");
  console.log();
  console.log("The call_id is returned by sendCall.js when you send a call.");
  console.log("Example: node getCall.js abc12345-def6-7890-ghij-klmnopqrstuv");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Fetch and display call details
// ---------------------------------------------------------------------------

async function getCallDetails() {
  console.log(`Fetching details for call: ${callId}`);
  console.log();

  try {
    // Make the GET request to the call details endpoint.
    // The call_id is included directly in the URL path.
    const response = await axios.get(`${BASE_URL}/calls/${callId}`, {
      headers: {
        Authorization: API_KEY,
      },
      timeout: 15000,
    });

    const data = response.data;

    // -------------------------------------------------------------------
    // Display call metadata
    // -------------------------------------------------------------------

    const separator = "=".repeat(60);

    console.log(separator);
    console.log("CALL DETAILS");
    console.log(separator);
    console.log();

    // Basic call information.
    console.log(`Call ID:       ${data.call_id || "N/A"}`);
    console.log(`Status:        ${data.status || "N/A"}`);
    console.log(`Completed:     ${data.completed ?? "N/A"}`);
    console.log(`Queue Status:  ${data.queue_status || "N/A"}`);
    console.log();

    // Phone numbers involved in the call.
    console.log(`To:            ${data.to || "N/A"}`);
    console.log(`From:          ${data.from || "N/A"}`);
    console.log(`Answered By:   ${data.answered_by || "N/A"}`);
    console.log();

    // Call duration and cost.
    if (data.call_length != null) {
      console.log(`Duration:      ${data.call_length.toFixed(1)} minutes`);
    } else {
      console.log("Duration:      N/A");
    }

    if (data.price != null) {
      console.log(`Cost:          $${data.price.toFixed(4)}`);
    } else {
      console.log("Cost:          N/A");
    }

    console.log();

    // -------------------------------------------------------------------
    // Display error information (if any)
    // -------------------------------------------------------------------

    if (data.error_message) {
      console.log(separator);
      console.log("ERROR");
      console.log(separator);
      console.log(data.error_message);
      console.log();
    }

    // -------------------------------------------------------------------
    // Display the recording URL (if recording was enabled)
    // -------------------------------------------------------------------

    if (data.recording_url) {
      console.log(`Recording URL: ${data.recording_url}`);
      console.log();
    }

    // -------------------------------------------------------------------
    // Display the full transcript
    // -------------------------------------------------------------------

    // The API returns the transcript in two formats:
    // 1. "transcripts" - An array of individual utterance objects with
    //    speaker labels and timestamps. Useful for programmatic processing.
    // 2. "concatenated_transcript" - The full transcript as a single string
    //    with speaker labels. Easier to read.

    if (data.concatenated_transcript) {
      console.log(separator);
      console.log("TRANSCRIPT");
      console.log(separator);
      console.log();
      console.log(data.concatenated_transcript);
      console.log();
    } else if (data.transcripts && data.transcripts.length > 0) {
      console.log(separator);
      console.log("TRANSCRIPT");
      console.log(separator);
      console.log();
      // Format each transcript entry with speaker labels.
      for (const entry of data.transcripts) {
        // Each transcript entry has a "user" field (either "agent" or "user")
        // and a "text" field with what was said.
        const speaker = (entry.user || "unknown").toUpperCase();
        const text = entry.text || "";
        console.log(`[${speaker}] ${text}`);
      }
      console.log();
    } else {
      console.log("No transcript available yet.");
      console.log(
        "If the call just ended, wait a few seconds and try again."
      );
      console.log();
    }

    // -------------------------------------------------------------------
    // Display the AI-generated summary
    // -------------------------------------------------------------------

    if (data.summary) {
      console.log(separator);
      console.log("SUMMARY");
      console.log(separator);
      console.log();
      console.log(data.summary);
      console.log();
    }

    // -------------------------------------------------------------------
    // Display extracted variables (if any)
    // -------------------------------------------------------------------

    // Variables can be extracted during the call based on your prompt
    // instructions. For example, if the agent is supposed to collect a
    // name and date, those values might appear here.

    const variables = data.variables;
    if (variables && Object.keys(variables).length > 0) {
      console.log(separator);
      console.log("EXTRACTED VARIABLES");
      console.log(separator);
      console.log();
      for (const [key, value] of Object.entries(variables)) {
        console.log(`  ${key}: ${value}`);
      }
      console.log();
    }

    // -------------------------------------------------------------------
    // Display the raw JSON (for debugging)
    // -------------------------------------------------------------------

    // Uncomment the lines below to see the full raw API response.
    // This is helpful for debugging or when you need to see every field.

    // console.log(separator);
    // console.log("RAW API RESPONSE");
    // console.log(separator);
    // console.log();
    // console.log(JSON.stringify(data, null, 2));
    // console.log();

    console.log(separator);
    console.log("Done.");
  } catch (error) {
    // Handle different types of errors with helpful messages.
    if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API.");
      console.error("Check your internet connection and try again.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The request timed out. Try again in a moment.");
    } else if (error.response) {
      // The API returned an error status code.
      const status = error.response.status;
      console.error(`Error: API returned status code ${status}.`);

      if (status === 404) {
        console.error("Call not found. Double check the call_id.");
      } else if (status === 401) {
        console.error("Invalid API key. Check your .env file.");
      } else {
        console.error(
          `Response: ${JSON.stringify(error.response.data, null, 2)}`
        );
      }
    } else {
      console.error(`Error: ${error.message}`);
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

getCallDetails();
