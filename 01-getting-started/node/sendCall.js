/**
 * Bland AI - Send Your First Call (Node.js)
 *
 * This script sends an outbound phone call using the Bland AI API.
 * The AI agent acts as a friendly restaurant reservation assistant
 * for "Bella's Italian Kitchen."
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key and phone number.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node sendCall.js
 *
 * The script will:
 *    - Send a call to the specified phone number
 *    - Print the call_id for tracking
 *    - Optionally poll until the call completes and print the result
 */

// Load environment variables from the .env file in this directory.
// This keeps your API key out of source control.
require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

// The phone number to call, in E.164 format (e.g., +15551234567).
const PHONE_NUMBER = process.env.PHONE_NUMBER;

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

if (!PHONE_NUMBER) {
  console.error("Error: PHONE_NUMBER is not set.");
  console.error(
    "Add your phone number in E.164 format to .env (e.g., +15551234567)."
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Define the agent prompt
// ---------------------------------------------------------------------------

// The "task" is the core instruction set for your AI agent. Think of it as the
// agent's personality, knowledge, and rules all in one prompt. The more
// specific and structured you make this, the better the agent will perform.
//
// Tips for writing great prompts:
//   - Give the agent a clear identity and role.
//   - Specify exactly what information to collect.
//   - Include example phrases and responses for common scenarios.
//   - Define boundaries (what the agent should NOT do).
//   - Use {{variable_name}} syntax to inject dynamic data via request_data.

const AGENT_TASK = `You are Bella, a warm and professional reservation assistant for Bella's Italian Kitchen,
a popular Italian restaurant in downtown Chicago.

Your goal is to help the caller make a dinner reservation. You should collect:
1. The number of guests (between 1 and 12; for parties larger than 12, let them know they need to call the events team)
2. The preferred date and time (dinner service runs from 5:00 PM to 10:00 PM, Tuesday through Sunday; closed on Mondays)
3. The name for the reservation
4. Any dietary restrictions or special requests (allergies, high chair needed, birthday celebration, etc.)

Important guidelines:
- Be friendly, warm, and conversational. Use a natural tone, not robotic.
- If someone asks about the menu, mention that you have classic Italian dishes including handmade pasta,
  wood-fired pizza, fresh seafood, and a curated wine list.
- If asked about pricing, mention that entrees range from $18 to $45.
- If the caller wants to speak with a manager or has a complaint, offer to transfer them.
- Confirm all reservation details before ending the call.
- Keep responses concise. One to two sentences at a time works best for phone conversations.

Example greeting: "Hi there! Thank you for calling Bella's Italian Kitchen. I'd love to help you with a reservation.
How many guests will be joining us?"`;

// ---------------------------------------------------------------------------
// Build the request payload
// ---------------------------------------------------------------------------

// This object contains all the parameters for the API call.
// Required fields are phone_number and task. Everything else is optional
// but helps you fine-tune the agent's behavior.

const payload = {
  // REQUIRED: The phone number to call in E.164 format.
  phone_number: PHONE_NUMBER,

  // REQUIRED: The prompt/instructions that define how the AI agent behaves.
  task: AGENT_TASK,

  // OPTIONAL: The voice the agent uses on the call.
  // Available voices: "mason", "maya", "ryan", "tina", "josh",
  //                   "florian", "derek", "june", "nat", "paige"
  // Each voice has a distinct tone and personality. Try a few to find
  // the best fit for your use case.
  voice: "maya",

  // OPTIONAL: The exact first sentence the agent says when the call connects.
  // If omitted, the agent generates its own greeting based on the task prompt.
  // Setting this explicitly ensures a consistent opening every time.
  first_sentence:
    "Hi there! Thank you for calling Bella's Italian Kitchen. " +
    "I'd love to help you with a reservation. How many guests will be joining us?",

  // OPTIONAL: Which model to use for generating responses.
  // "base"  - Full-featured model with all capabilities.
  // "turbo" - Lowest latency, but some advanced features may not be available.
  model: "base",

  // OPTIONAL: The language for the call. Default is "babel-en" (English).
  // Bland supports 40+ languages. Change this if you need a different language.
  language: "babel-en",

  // OPTIONAL: Maximum call length in minutes. The call automatically ends
  // after this duration. Default is 30 minutes. Set this to prevent
  // unexpectedly long (and expensive) calls.
  max_duration: 5,

  // OPTIONAL: Whether to record the call. When true, a recording_url will
  // be available in the call details after the call completes.
  record: true,

  // OPTIONAL: Controls the randomness of the agent's responses.
  // 0.0 = very deterministic and consistent responses.
  // 1.0 = more creative and varied responses.
  // 0.7 is a good balance for most conversational use cases.
  temperature: 0.7,

  // OPTIONAL: If true, the agent waits silently for the human to speak
  // before saying anything. Useful for inbound-style calls where you want
  // the human to initiate the conversation.
  wait_for_greeting: false,

  // OPTIONAL: A phone number to transfer the call to if the human asks
  // to speak with a real person. Uncomment and set this if you want to
  // enable live transfers.
  // transfer_phone_number: "+15559876543",

  // OPTIONAL: A URL that receives a POST request with the full call data
  // when the call completes. Useful for integrating with your backend
  // without needing to poll the API.
  // webhook: "https://your-server.com/api/bland-webhook",

  // OPTIONAL: Custom key-value pairs that you can reference in the task
  // prompt using {{variable_name}} syntax. Great for personalizing calls.
  // For example, if you set "customer_name": "Sarah" here, you can use
  // {{customer_name}} in the task prompt and it will be replaced with "Sarah".
  request_data: {
    restaurant_name: "Bella's Italian Kitchen",
    location: "downtown Chicago",
  },

  // OPTIONAL: Controls what happens when the call goes to voicemail.
  // "action" can be:
  //   "hangup"        - End the call immediately.
  //   "leave_message" - Leave the specified message.
  //   "ignore"        - Continue as if speaking to a person.
  voicemail: {
    action: "leave_message",
    message:
      "Hi, this is Bella's Italian Kitchen calling. " +
      "We'd love to help you make a reservation. " +
      "Please call us back at your convenience. Thank you!",
  },

  // OPTIONAL: Ambient background audio for the call. Adds a layer of
  // realism to the conversation.
  // Options: null (no background), "office", "cafe", "restaurant", "none"
  background_track: "restaurant",
};

// ---------------------------------------------------------------------------
// Send the call
// ---------------------------------------------------------------------------

async function sendCall() {
  console.log(`Sending call to ${PHONE_NUMBER}...`);
  console.log();

  try {
    // Make the POST request to the Send Call endpoint.
    // The Authorization header uses your API key directly (no "Bearer" prefix).
    const response = await axios.post(`${BASE_URL}/calls`, payload, {
      headers: {
        Authorization: API_KEY,
        "Content-Type": "application/json",
      },
      timeout: 30000, // 30-second timeout for the HTTP request itself
    });

    const data = response.data;

    // Check if the call was successfully queued.
    if (data.status === "success") {
      const callId = data.call_id;
      console.log("Call successfully queued!");
      console.log(`Call ID: ${callId}`);
      console.log();
      console.log(
        "Your phone should ring shortly. Answer it to talk with the AI agent."
      );
      console.log();
      console.log("To retrieve call details after it ends, run:");
      console.log(`  node getCall.js ${callId}`);
    } else {
      // If the status is not "success", print the full response for debugging.
      console.error("Unexpected response from API:");
      console.error(JSON.stringify(data, null, 2));
      process.exit(1);
    }
  } catch (error) {
    // Handle different types of errors with helpful messages.
    if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API.");
      console.error("Check your internet connection and try again.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The request timed out.");
      console.error(
        "The Bland API may be experiencing high traffic. Try again in a moment."
      );
    } else if (error.response) {
      // The API returned an error status code (4xx, 5xx).
      console.error(
        `Error: API returned status code ${error.response.status}.`
      );
      console.error(
        `Response: ${JSON.stringify(error.response.data, null, 2)}`
      );
    } else {
      // Some other unexpected error.
      console.error(`Error: ${error.message}`);
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Optional: Poll for call completion
// ---------------------------------------------------------------------------

// Uncomment the function below and the call to it at the bottom of the file
// if you want the script to wait for the call to finish and print the results
// automatically. In production, you would typically use a webhook instead.

// async function pollForCompletion(callId) {
//   console.log();
//   console.log("Waiting for call to complete...");
//   console.log("(Press Ctrl+C to stop polling and exit)");
//   console.log();
//
//   const MAX_POLL_TIME = 300;   // Maximum time to poll in seconds (5 minutes)
//   const POLL_INTERVAL = 5;     // Seconds between each poll request
//   let elapsed = 0;
//
//   while (elapsed < MAX_POLL_TIME) {
//     try {
//       // Fetch the current call details.
//       const response = await axios.get(`${BASE_URL}/calls/${callId}`, {
//         headers: { Authorization: API_KEY },
//         timeout: 15000,
//       });
//
//       const data = response.data;
//
//       // Check if the call has completed.
//       if (data.completed) {
//         console.log("Call completed!");
//         console.log();
//         console.log(`Duration: ${(data.call_length || 0).toFixed(1)} minutes`);
//         console.log(`Answered by: ${data.answered_by || "unknown"}`);
//         console.log(`Cost: $${(data.price || 0).toFixed(4)}`);
//         console.log();
//
//         // Print the transcript if available.
//         if (data.concatenated_transcript) {
//           console.log("Transcript:");
//           console.log("-".repeat(60));
//           console.log(data.concatenated_transcript);
//           console.log("-".repeat(60));
//           console.log();
//         }
//
//         // Print the summary if available.
//         if (data.summary) {
//           console.log("Summary:");
//           console.log(data.summary);
//           console.log();
//         }
//
//         return;
//       }
//
//       // Print a progress update and wait before polling again.
//       console.log(`  Status: ${data.status || "unknown"} (${elapsed}s elapsed)`);
//       await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL * 1000));
//       elapsed += POLL_INTERVAL;
//
//     } catch (err) {
//       console.error(`  Poll error: ${err.message}. Retrying...`);
//       await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL * 1000));
//       elapsed += POLL_INTERVAL;
//     }
//   }
//
//   console.log(`Polling timed out after ${MAX_POLL_TIME} seconds.`);
//   console.log("The call may still be in progress. Use getCall.js to check later.");
// }

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

sendCall();

// To enable polling, uncomment the line below and the pollForCompletion
// function above. Replace sendCall() above with:
//
// sendCall().then((callId) => {
//   if (callId) return pollForCompletion(callId);
// });
