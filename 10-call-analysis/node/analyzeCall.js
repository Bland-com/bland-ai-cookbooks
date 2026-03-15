/**
 * Bland AI - Analyze a Call (Node.js)
 *
 * This script fetches the details of a specific call and then runs AI-powered
 * analysis on the transcript. It asks practical questions about the call and
 * displays the structured answers.
 *
 * Usage:
 *     1. Copy .env.example to .env and fill in your API key.
 *     2. Install dependencies: npm install axios dotenv
 *     3. Run with a specific call ID:
 *            node analyzeCall.js <call_id>
 *        Or run without arguments to analyze your most recent call:
 *            node analyzeCall.js
 *
 * The script will:
 *     - Fetch the call details and display basic metadata
 *     - Send the call transcript to the AI analysis endpoint
 *     - Display the analysis results in a readable format
 */

const axios = require("axios");

// Load environment variables from the .env file in this directory.
// This keeps your API key out of source control.
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
// The key is sent in the Authorization header of every request.
const API_KEY = process.env.BLAND_API_KEY;

// The Bland API base URL. All endpoints are under this path.
const BASE_URL = "https://api.bland.ai/v1";

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
  "Content-Type": "application/json",
};

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

/**
 * Fetches call details, displays basic metadata, runs AI analysis,
 * and prints the structured results.
 */
async function analyzeCall() {
  // -------------------------------------------------------------------
  // Determine the call ID to analyze
  // -------------------------------------------------------------------

  // The call_id can be passed as a command-line argument (process.argv[2]).
  // If no argument is provided, the script fetches the most recent call.
  let callId = process.argv[2] || null;

  if (!callId) {
    // No call_id provided. Fetch the most recent call from the list endpoint.
    console.log("No call_id provided. Fetching your most recent call...");
    console.log();

    try {
      // GET /v1/calls returns an array of recent calls.
      // We grab the first one (most recent) and use its call_id.
      const listResponse = await axios.get(BASE_URL + "/calls", {
        headers,
        timeout: 15000,
      });

      // The response may be a bare array or an object wrapping the calls.
      let calls = listResponse.data;
      if (typeof calls === "object" && !Array.isArray(calls)) {
        calls = calls.calls || [];
      }

      if (!calls || calls.length === 0) {
        console.log("No calls found on your account.");
        console.log("Send a test call first using the getting-started cookbook.");
        process.exit(1);
      }

      // Use the first call in the list (most recent).
      callId = calls[0].call_id;
      console.log("Using most recent call: " + callId);
      console.log();
    } catch (error) {
      console.error("Error fetching call list: " + (error.message || error));
      process.exit(1);
    }
  }

  // -------------------------------------------------------------------
  // Fetch call details
  // -------------------------------------------------------------------

  console.log("Fetching details for call: " + callId);
  console.log();

  let callData;

  try {
    // GET /v1/calls/{call_id} returns the full details for a single call.
    // This includes the transcript, summary, duration, cost, variables, and more.
    const response = await axios.get(BASE_URL + "/calls/" + callId, {
      headers,
      timeout: 15000,
    });
    callData = response.data;
  } catch (error) {
    if (error.response) {
      console.error("Error: API returned status code " + error.response.status + ".");
      if (error.response.status === 404) {
        console.error("Call not found. Double check the call_id.");
      } else if (error.response.status === 401) {
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
  // Display basic call information
  // -------------------------------------------------------------------

  console.log("=".repeat(60));
  console.log("CALL DETAILS");
  console.log("=".repeat(60));
  console.log();

  // Basic metadata about the call.
  console.log("Call ID:       " + (callData.call_id || "N/A"));
  console.log("Status:        " + (callData.status || "N/A"));
  console.log("Completed:     " + (callData.completed != null ? callData.completed : "N/A"));
  console.log();

  // Phone numbers and direction.
  console.log("To:            " + (callData.to || "N/A"));
  console.log("From:          " + (callData.from || "N/A"));
  console.log("Inbound:       " + (callData.inbound != null ? callData.inbound : "N/A"));
  console.log("Answered By:   " + (callData.answered_by || "N/A"));
  console.log("Ended By:      " + (callData.call_ended_by || "N/A"));
  console.log();

  // Duration and cost.
  if (callData.call_length != null) {
    console.log("Duration:      " + callData.call_length.toFixed(1) + " minutes");
  } else {
    console.log("Duration:      N/A");
  }

  if (callData.price != null) {
    console.log("Cost:          $" + callData.price.toFixed(4));
  } else {
    console.log("Cost:          N/A");
  }

  console.log();

  // Show the recording URL if the call was recorded.
  if (callData.recording_url) {
    console.log("Recording:     " + callData.recording_url);
    console.log();
  }

  // Show the AI-generated summary if available.
  if (callData.summary) {
    console.log("Summary:");
    console.log("  " + callData.summary);
    console.log();
  }

  // Show any extracted variables from the call.
  const variables = callData.variables || {};
  if (Object.keys(variables).length > 0) {
    console.log("Variables:");
    for (const [key, value] of Object.entries(variables)) {
      console.log("  " + key + ": " + value);
    }
    console.log();
  }

  // Show the transcript preview (first few lines).
  const concatenated = callData.concatenated_transcript || "";
  if (concatenated) {
    console.log("Transcript Preview:");
    // Show the first 500 characters of the transcript as a preview.
    let preview = concatenated.substring(0, 500);
    if (concatenated.length > 500) {
      preview += "...";
    }
    console.log("  " + preview);
    console.log();
  }

  // -------------------------------------------------------------------
  // Run AI analysis on the call
  // -------------------------------------------------------------------

  // The analysis endpoint lets you ask natural-language questions about a call
  // and get structured, typed answers back. Each question is a two-element
  // array: [question_text, expected_answer_type].
  //
  // Supported answer types:
  //   "string"   - Returns a free-text answer.
  //   "boolean"  - Returns true or false.
  //   "number"   - Returns a numeric value.
  //   Custom     - Returns one of the values in the string (e.g., "human or voicemail").
  //
  // If a question cannot be answered from the transcript, the answer is null.

  console.log("=".repeat(60));
  console.log("AI ANALYSIS");
  console.log("=".repeat(60));
  console.log();
  console.log("Running AI analysis on the call transcript...");
  console.log();

  // Define the analysis request.
  // The "goal" gives the AI context about what you are trying to evaluate.
  // The "questions" array contains the specific questions to answer.
  const analysisPayload = {
    // The goal provides high-level context for the analysis.
    // It helps the AI understand the purpose of your questions so it can
    // give more relevant and accurate answers.
    goal:
      "Evaluate the quality and outcome of this customer interaction",

    // Each question is a two-element array: [question_text, answer_type].
    // The answer_type tells the AI what format to return.
    questions: [
      // Boolean question: returns true or false.
      // Useful for yes/no determinations about the call.
      ["Did the customer express interest in the product or service?", "boolean"],

      // String question: returns a free-text answer.
      // Good for extracting specific details or open-ended insights.
      ["What was the customer's primary concern or request?", "string"],

      // Boolean question: checks whether an objective was achieved.
      ["Was the customer's issue or request resolved?", "boolean"],

      // Number question: returns a numeric score.
      // The AI infers the number from the conversation tone and content.
      ["How would you rate the customer's satisfaction on a scale of 1 to 10?", "number"],

      // Custom answer type: returns one of the specified values.
      // Useful when you want the answer constrained to specific options.
      ["Was the call answered by a human or voicemail?", "human or voicemail"],
    ],
  };

  let analysisData;

  try {
    // POST /v1/calls/{call_id}/analyze sends the questions to the AI and
    // returns structured answers based on the call transcript.
    const analysisResponse = await axios.post(
      BASE_URL + "/calls/" + callId + "/analyze",
      analysisPayload,
      {
        headers,
        timeout: 30000, // Analysis can take a few seconds for long transcripts.
      }
    );
    analysisData = analysisResponse.data;
  } catch (error) {
    if (error.response) {
      console.error(
        "Error: Analysis API returned status code " + error.response.status + "."
      );
      console.error("Response: " + JSON.stringify(error.response.data));
    } else if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API for analysis.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The analysis request timed out.");
      console.error("This can happen with very long transcripts. Try again.");
    } else {
      console.error("Error: " + error.message);
    }
    process.exit(1);
  }

  // -------------------------------------------------------------------
  // Display analysis results
  // -------------------------------------------------------------------

  // Check if the analysis was successful.
  if (analysisData.status === "success") {
    // The "answers" array corresponds to the "questions" array by index.
    // answers[0] is the answer to questions[0], answers[1] to questions[1], etc.
    const answers = analysisData.answers || [];

    // The questions we asked, for display purposes.
    const questions = analysisPayload.questions;

    // Print each question with its answer in a readable format.
    for (let i = 0; i < questions.length; i++) {
      const questionText = questions[i][0]; // The question string
      const answerType = questions[i][1];   // The expected answer type

      // Get the corresponding answer, defaulting to "N/A" if missing.
      let answer = i < answers.length ? answers[i] : "N/A";

      // Format null answers as a readable string.
      if (answer === null) {
        answer = "(could not be determined from transcript)";
      }

      // Format boolean answers for readability.
      if (typeof answer === "boolean") {
        answer = answer ? "Yes" : "No";
      }

      console.log("Q: " + questionText);
      console.log("   Type: " + answerType);
      console.log("   A: " + answer);
      console.log();
    }

    // Show the credits used for this analysis.
    // Base cost: 0.003 credits, plus 0.0015 per call, adjusted for length.
    const creditsUsed = analysisData.credits_used || 0;
    console.log("Credits used for analysis: " + creditsUsed);
    console.log();
  } else {
    // The analysis failed or returned an unexpected status.
    console.log("Analysis was not successful.");
    console.log("Response:");
    console.log(JSON.stringify(analysisData, null, 2));
    console.log();
  }

  // -------------------------------------------------------------------
  // Done
  // -------------------------------------------------------------------

  console.log("=".repeat(60));
  console.log("Done.");
}

// Run the main function.
analyzeCall();
