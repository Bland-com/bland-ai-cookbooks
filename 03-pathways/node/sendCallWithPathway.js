/**
 * sendCallWithPathway.js
 *
 * Sends a phone call using an existing Bland AI pathway. Instead of providing
 * a task prompt, you reference a pathway_id and the agent follows the
 * structured conversation flow defined in the pathway.
 *
 * You can also pass request_data to pre-populate variables that the pathway
 * can use from the very start of the call.
 *
 * Usage:
 *   1. Copy .env.example to .env and fill in your API key, pathway ID, and phone number
 *   2. npm install axios dotenv
 *   3. node sendCallWithPathway.js
 *
 * Prerequisites:
 *   Run createPathway.js first to get a pathway_id, or use one from the dashboard.
 */

const axios = require("axios");
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland AI API key
const BLAND_API_KEY = process.env.BLAND_API_KEY;

// The pathway ID to use for this call.
// You get this from createPathway.js or from the Bland dashboard.
const PATHWAY_ID = process.env.PATHWAY_ID;

// The phone number to call. Must be in E.164 format (e.g., +12223334444).
const PHONE_NUMBER = process.env.PHONE_NUMBER;

// Base URL and headers for the Bland API
const BASE_URL = "https://api.bland.ai/v1";
const HEADERS = {
  Authorization: BLAND_API_KEY,
  "Content-Type": "application/json",
};

/**
 * Send a phone call that uses a pathway instead of a simple task prompt.
 *
 * POST https://api.bland.ai/v1/calls
 * Body: {
 *   phone_number: "+1...",
 *   pathway_id: "uuid",
 *   request_data: { ... }
 * }
 *
 * Key differences from a regular task-based call:
 *   - Use "pathway_id" instead of "task"
 *   - The agent follows the node/edge structure of the pathway
 *   - You can pass "request_data" to inject variables into the pathway
 *     before the call starts (useful for personalization)
 *
 * Returns the call_id which you can use to check call status and
 * retrieve the transcript later.
 */
async function sendCallWithPathway() {
  const url = `${BASE_URL}/calls`;

  const payload = {
    // The phone number to dial. Must include country code.
    phone_number: PHONE_NUMBER,

    // The pathway_id tells Bland to use a structured pathway
    // instead of a freeform task prompt. The agent will start
    // at the node marked isStart: true and follow edges based
    // on the conversation.
    pathway_id: PATHWAY_ID,

    // request_data lets you pass variables into the pathway before
    // the call even starts. These become available as {{variable_name}}
    // in any node prompt.
    //
    // This is useful for personalization. For example, if you know the
    // caller's name from your CRM, you can pass it here and reference
    // it in your greeting node with {{customer_name}}.
    request_data: {
      restaurant_name: "Mario's Italian Kitchen",
      customer_name: "Valued Guest",
    },

    // voice_id: Optionally specify which voice the agent should use.
    // Browse available voices at https://app.bland.ai/voices
    // Uncomment and set a voice ID if you want a specific voice:
    // voice_id: "your-voice-id-here",

    // max_duration: Maximum call length in minutes. The call will
    // automatically end after this many minutes. Default is 30.
    // Set lower for testing to avoid accidental long calls.
    max_duration: 5,

    // record: Whether to record the call audio. Defaults to true.
    // The recording URL will be available in the call details after
    // the call ends.
    record: true,
  };

  console.log(
    `Sending call to ${PHONE_NUMBER} using pathway ${PATHWAY_ID}...`
  );
  const response = await axios.post(url, payload, { headers: HEADERS });

  const data = response.data;
  const callId = data.call_id;

  console.log(`\nCall dispatched successfully!`);
  console.log(`Call ID: ${callId}`);
  console.log(`\nFull response:\n${JSON.stringify(data, null, 2)}`);
  console.log(`\nThe call is now in progress. You can check its status with:`);
  console.log(`  GET ${BASE_URL}/calls/${callId}`);

  return data;
}

/**
 * Validate configuration and send the call.
 */
async function main() {
  // Check that all required environment variables are set
  const missing = [];
  if (!BLAND_API_KEY) missing.push("BLAND_API_KEY");
  if (!PATHWAY_ID) missing.push("PATHWAY_ID");
  if (!PHONE_NUMBER) missing.push("PHONE_NUMBER");

  if (missing.length > 0) {
    console.error("Error: Missing required environment variables:");
    missing.forEach((v) => console.error(`  - ${v}`));
    console.error("\nCopy .env.example to .env and fill in the values.");
    console.error("Run createPathway.js first to get a PATHWAY_ID.");
    return;
  }

  try {
    await sendCallWithPathway();
  } catch (error) {
    // Axios errors include the response data which often has helpful details
    if (error.response) {
      console.error(`API Error (${error.response.status}):`);
      console.error(JSON.stringify(error.response.data, null, 2));
    } else {
      console.error("Error:", error.message);
    }
  }
}

main();
