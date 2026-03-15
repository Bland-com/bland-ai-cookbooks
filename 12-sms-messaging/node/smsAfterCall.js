/**
 * Bland AI - Send an SMS Follow-Up After a Phone Call (Node.js)
 *
 * This script demonstrates a common workflow: after an AI phone call completes,
 * send an SMS follow-up to the customer with a summary, next steps, or a
 * confirmation of what was discussed.
 *
 * The workflow:
 *   1. Send a phone call with an analysis_schema to extract key details.
 *   2. Wait for the call to complete.
 *   3. Read the extracted data (customer name, email, follow-up preferences).
 *   4. Send a personalized SMS to the customer based on the call outcome.
 *
 * This is one of the most powerful patterns in Bland: combining voice calls
 * with automated SMS follow-ups so no lead or customer falls through the cracks.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key and phone numbers.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node smsAfterCall.js
 *
 * Note: SMS messaging is an Enterprise feature. Your Bland phone number
 * must be configured for SMS, and US numbers require A2P 10DLC registration.
 */

require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

// The phone number to call AND text. We call first, then text a summary.
const TO_NUMBER = process.env.TO_NUMBER;

// Your Bland phone number (must be configured for both voice and SMS).
const FROM_NUMBER = process.env.FROM_NUMBER;

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

if (!TO_NUMBER) {
  console.error("Error: TO_NUMBER is not set.");
  console.error("Add the recipient's phone number in E.164 format to .env.");
  process.exit(1);
}

if (!FROM_NUMBER) {
  console.error("Error: FROM_NUMBER is not set.");
  console.error("Add your Bland phone number (voice + SMS configured) to .env.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// HTTP headers
// ---------------------------------------------------------------------------

const headers = {
  Authorization: API_KEY,
  "Content-Type": "application/json",
};

// ---------------------------------------------------------------------------
// Helper: sleep for N milliseconds
// ---------------------------------------------------------------------------

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

async function smsAfterCall() {
  console.log("=".repeat(60));
  console.log("VOICE CALL + SMS FOLLOW-UP WORKFLOW");
  console.log("=".repeat(60));
  console.log();

  // =========================================================================
  // Step 1: Send the phone call
  // =========================================================================

  const callPayload = {
    phone_number: TO_NUMBER,
    from: FROM_NUMBER,
    task: `You are Jamie from Greenfield Insurance, calling to discuss
a customer's auto insurance renewal. Their policy is up for renewal next month.

Your goals:
1. Greet the customer and let them know their policy is renewing soon.
2. Ask if they want to keep the same coverage or if anything has changed
   (new car, new driver, address change).
3. Mention that you can offer a multi-policy discount if they bundle home
   and auto insurance.
4. Ask if they have any questions about their coverage.
5. Let them know you will send a follow-up text with a summary and a link
   to review their policy online.
6. Thank them and wrap up.

Keep the conversation professional and helpful. If they want to make changes,
note what they want changed and let them know you will include it in the
follow-up text.`,
    analysis_schema: {
      customer_name: "The customer's name.",
      wants_changes:
        "Does the customer want to make any changes to their policy? " +
        "true or false.",
      requested_changes:
        "If they want changes, describe what they requested. " +
        "Null if no changes.",
      interested_in_bundle:
        "Is the customer interested in a multi-policy bundle discount? " +
        "true, false, or maybe.",
      has_questions:
        "Did the customer have any unresolved questions? true or false.",
      question_summary:
        "Brief summary of any questions the customer asked. " +
        "Null if no questions.",
    },
    record: true,
    max_duration: 5,
  };

  console.log("Step 1: Sending phone call to " + TO_NUMBER + "...");
  console.log();

  let callId;

  try {
    const callResponse = await axios.post(BASE_URL + "/calls", callPayload, {
      headers,
      timeout: 30000,
    });

    callId = callResponse.data.call_id;

    if (!callId) {
      console.error("Error: No call_id returned.");
      console.error(JSON.stringify(callResponse.data, null, 2));
      process.exit(1);
    }

    console.log("Call queued! Call ID: " + callId);
    console.log();
  } catch (error) {
    console.error("Error sending call: " + (error.message || error));
    if (error.response) {
      console.error("Response: " + JSON.stringify(error.response.data, null, 2));
    }
    process.exit(1);
  }

  // =========================================================================
  // Step 2: Wait for the call to complete
  // =========================================================================

  console.log("Step 2: Waiting for the call to complete...");
  console.log("(Answer your phone when it rings!)");
  console.log();

  let callCompleted = false;

  for (let attempt = 0; attempt < 60; attempt++) {
    try {
      const pollResponse = await axios.get(BASE_URL + "/calls/" + callId, {
        headers,
        timeout: 15000,
      });
      const pollData = pollResponse.data;

      if (pollData.completed || pollData.status === "completed") {
        console.log("Call completed!");
        console.log();
        callCompleted = true;
        break;
      }

      const elapsed = (attempt + 1) * 5;
      console.log("  Waiting... (" + elapsed + "s)");
    } catch (_) {
      // Ignore transient errors during polling.
    }

    await sleep(5000);
  }

  if (!callCompleted) {
    console.log("Timed out. Check the dashboard for results.");
    process.exit(0);
  }

  // =========================================================================
  // Step 3: Read the analysis results
  // =========================================================================

  console.log("Step 3: Reading call analysis...");
  console.log();

  let result;

  try {
    const resultResponse = await axios.get(BASE_URL + "/calls/" + callId, {
      headers,
      timeout: 15000,
    });
    result = resultResponse.data;
  } catch (error) {
    console.error("Error reading results: " + error.message);
    process.exit(1);
  }

  const analysis = result.analysis || {};
  const summary = result.summary || "";

  console.log("Call Summary:");
  if (summary) {
    console.log("  " + summary);
  } else {
    console.log("  (No summary available)");
  }
  console.log();

  console.log("Extracted Data:");
  for (const [key, value] of Object.entries(analysis)) {
    console.log("  " + key + ": " + value);
  }
  console.log();

  // =========================================================================
  // Step 4: Send an SMS follow-up based on the call outcome
  // =========================================================================

  console.log("Step 4: Sending SMS follow-up...");
  console.log();

  // Build a personalized SMS based on what was discussed.
  const customerName = analysis.customer_name || "there";
  const wantsChanges = analysis.wants_changes;
  const requestedChanges = analysis.requested_changes;
  const interestedInBundle = analysis.interested_in_bundle;
  const hasQuestions = analysis.has_questions;
  const questionSummary = analysis.question_summary;

  const smsLines = [
    "Hi " + customerName + "! This is Jamie from Greenfield Insurance.",
    "Thanks for chatting about your policy renewal today.",
  ];

  if (wantsChanges && requestedChanges) {
    smsLines.push(
      "I have noted your requested changes: " +
        requestedChanges +
        ". Our team will update your policy and send a revised quote " +
        "within 1 business day."
    );
  } else if (wantsChanges === false) {
    smsLines.push(
      "Your current coverage will renew as-is next month. " +
        "No action needed on your end."
    );
  }

  if (interestedInBundle === "true" || interestedInBundle === true) {
    smsLines.push(
      "I will also have our team put together a bundle quote " +
        "for home + auto. We will email that over shortly."
    );
  }

  if (hasQuestions && questionSummary) {
    smsLines.push(
      "Regarding your question about " +
        questionSummary +
        ", I will have a specialist follow up with more details."
    );
  }

  smsLines.push("Reply to this text anytime if you need anything else!");

  const smsMessage = smsLines.join(" ");

  console.log("SMS Message:");
  console.log("  " + smsMessage);
  console.log();

  const smsPayload = {
    phone_number: TO_NUMBER,
    from: FROM_NUMBER,
    message: smsMessage,
  };

  try {
    const smsResponse = await axios.post(BASE_URL + "/sms/send", smsPayload, {
      headers,
      timeout: 30000,
    });

    console.log("SMS sent successfully!");
    console.log("Response: " + JSON.stringify(smsResponse.data, null, 2));
    console.log();
  } catch (error) {
    if (error.response) {
      console.error(
        "Error sending SMS: status " + error.response.status
      );
      console.error(JSON.stringify(error.response.data, null, 2));
    } else {
      console.error("Error sending SMS: " + error.message);
    }
    console.log();
    console.log("Note: SMS is an Enterprise feature. If you see a 403 error,");
    console.log("contact Bland support to enable SMS on your account.");
    console.log();
  }

  // =========================================================================
  // Done
  // =========================================================================

  console.log("=".repeat(60));
  console.log("WORKFLOW COMPLETE");
  console.log("=".repeat(60));
  console.log();
  console.log("  1. Phone call completed (Call ID: " + callId + ")");
  console.log("  2. Structured data extracted via analysis_schema");
  console.log("  3. Personalized SMS follow-up sent to " + TO_NUMBER);
  console.log();
  console.log("This workflow can run automatically via webhooks in production.");
  console.log("When the call webhook fires, your server reads the analysis data");
  console.log("and sends the SMS follow-up immediately, with no polling needed.");
  console.log();
  console.log("Done.");
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

smsAfterCall();
