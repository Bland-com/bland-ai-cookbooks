/**
 * Bland AI - Send a Call with a Persona (Node.js)
 *
 * This script sends an outbound phone call using a persona_id, which means
 * the persona's voice, prompt, model, and behavior settings serve as the
 * baseline configuration for the call. You can also override specific
 * persona settings on a per-call basis by including additional parameters.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key, phone number,
 *       and persona_id (from running createPersona.js).
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node sendCallWithPersona.js
 *
 * The script will:
 *    - Send a call using the persona's configuration as the baseline
 *    - Demonstrate how to override specific persona settings
 *    - Print the call_id for tracking
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

// The persona ID to use for this call. This was returned when you created
// the persona using createPersona.js. All of the persona's settings
// (voice, prompt, model, interruption threshold, etc.) are applied
// automatically as the baseline for the call.
const PERSONA_ID = process.env.PERSONA_ID;

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

if (!PERSONA_ID) {
  console.error("Error: PERSONA_ID is not set.");
  console.error(
    "Run createPersona.js first to create a persona, then add the"
  );
  console.error("persona_id to your .env file.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Build the request payload
// ---------------------------------------------------------------------------

// When using a persona_id, the persona's configuration serves as the
// baseline for the call. You only need to provide the phone_number and
// persona_id. The persona's voice, prompt, model, and all other settings
// are applied automatically.
//
// However, you can override any persona setting by including additional
// parameters in the request body. Parameters you include here take
// precedence over the persona defaults.

const payload = {
  // REQUIRED: The phone number to call in E.164 format.
  phone_number: PHONE_NUMBER,

  // REQUIRED: The persona ID. This tells the API to use the persona's
  // configuration (voice, prompt, model, etc.) as the baseline for
  // this call. You created this persona using createPersona.js.
  persona_id: PERSONA_ID,

  // -------------------------------------------------------------------------
  // OPTIONAL OVERRIDES
  // -------------------------------------------------------------------------
  // Any parameters you include below will override the persona's defaults
  // for this specific call. The persona itself is not modified.
  // Uncomment any of these to override the persona settings.

  // Override the first sentence for this specific call.
  // This replaces the persona's default greeting with a more targeted one.
  // Useful when you know the reason for the call ahead of time.
  // first_sentence: "Hi! I am calling about your recent support ticket.",

  // Override the maximum call duration for this specific call.
  // The persona may not have a max_duration set, or you may want a
  // different limit for this particular call.
  max_duration: 10,

  // Enable recording for this specific call. When true, a recording_url
  // will be available in the call details after the call completes.
  // This is a per-call setting that does not affect the persona.
  record: true,

  // Pass dynamic data that can be referenced in the persona's prompt
  // using {{variable_name}} syntax. This is a powerful way to personalize
  // calls without modifying the persona itself.
  request_data: {
    customer_name: "Alex Johnson",
    account_email: "alex.johnson@example.com",
    ticket_number: "TC-2024-4521",
  },

  // Override voicemail behavior for this specific call.
  // This controls what happens if the call goes to voicemail.
  voicemail: {
    // "hangup" ends the call immediately when voicemail is detected.
    // "leave_message" leaves the specified message.
    // "ignore" continues as if speaking to a person.
    action: "leave_message",
    message:
      "Hi, this is Sarah from TechCorp Customer Success. " +
      "I was calling to check in on your recent support request. " +
      "Please call us back at your convenience, or reply to the " +
      "email we sent. Thank you!",
  },

  // Add a pronunciation guide for words the agent might mispronounce.
  // This is especially useful for brand names, product names, acronyms,
  // and technical terms.
  pronunciation_guide: [
    {
      // The word to match in the agent's output text.
      word: "TechCorp",
      // How the agent should say it. Write it phonetically.
      pronunciation: "Tek-corp",
      // If true, only matches the exact casing ("TechCorp" but not
      // "techcorp"). If false, matches regardless of case.
      case_sensitive: true,
      // If true, the word is spelled out letter by letter.
      // If false, it is spoken as a single word.
      spaced: false,
    },
    {
      word: "SSO",
      pronunciation: "S-S-O",
      case_sensitive: false,
      // Spaced is true here because we want each letter pronounced
      // individually: "S, S, O" rather than "sso".
      spaced: true,
    },
  ],
};

// ---------------------------------------------------------------------------
// Send the call
// ---------------------------------------------------------------------------

async function sendCallWithPersona() {
  // Set the authorization header. Bland uses a simple API key in the
  // Authorization header (no "Bearer" prefix needed).
  const headers = {
    Authorization: API_KEY,
    "Content-Type": "application/json",
  };

  console.log(`Sending call with persona: ${PERSONA_ID}`);
  console.log(`Calling: ${PHONE_NUMBER}`);
  console.log();

  try {
    // Make the POST request to the Send Call endpoint.
    // The persona_id tells the API to load the persona's configuration
    // as the baseline. Any additional parameters in the payload override
    // the persona's defaults for this call only.
    const response = await axios.post(`${BASE_URL}/calls`, payload, {
      headers,
      timeout: 30000, // 30-second timeout for the HTTP request itself
    });

    // Extract the response data.
    const data = response.data;

    // Check if the call was successfully queued.
    if (data.status === "success") {
      const callId = data.call_id;
      console.log("Call successfully queued!");
      console.log();
      console.log(`  Call ID:    ${callId}`);
      console.log(`  Persona:   ${PERSONA_ID}`);
      console.log(`  Phone:     ${PHONE_NUMBER}`);
      console.log("  Recording: Enabled");
      console.log();
      console.log(
        "Your phone should ring shortly. Answer it to talk with the AI agent."
      );
      console.log(
        "The agent will use the persona's voice, prompt, and behavior settings."
      );
      console.log();
      console.log("After the call, check the Bland dashboard to review:");
      console.log("  - Full transcript");
      console.log(
        "  - Post-call analysis (based on the persona's analysis_schema)"
      );
      console.log("  - Recording (since record=true)");
      console.log();

      // -------------------------------------------------------------------
      // Demonstrate how to fetch the persona details for verification
      // -------------------------------------------------------------------

      console.log("Verifying persona configuration...");
      console.log();

      try {
        // Fetch the persona details to confirm the configuration.
        // This GET request returns the full persona object, including
        // all settings that will be used as the baseline for the call.
        const personaResponse = await axios.get(
          `${BASE_URL}/personas/${PERSONA_ID}`,
          {
            headers: { Authorization: API_KEY },
            timeout: 15000,
          }
        );
        const personaData = personaResponse.data;

        // Display key persona settings so the user can verify them.
        console.log("Persona details:");
        console.log(`  Name:        ${personaData.name || "Unknown"}`);
        console.log(`  Voice:       ${personaData.voice || "Unknown"}`);
        console.log(`  Model:       ${personaData.model || "Unknown"}`);
        console.log(`  Language:    ${personaData.language || "Unknown"}`);
        console.log();
      } catch (personaError) {
        // If we cannot fetch the persona details, it is not critical.
        // The call has already been queued successfully.
        console.log(
          "Could not fetch persona details (non-critical). The call"
        );
        console.log(
          "has been queued and will use the persona's configuration."
        );
        console.log();
      }
    } else {
      // If the status is not "success", print the full response for debugging.
      console.error("Unexpected response from API:");
      console.error(JSON.stringify(data, null, 2));
      process.exit(1);
    }
  } catch (error) {
    // Handle different types of errors with specific messages.
    if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API.");
      console.error("Check your internet connection and try again.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The request timed out.");
      console.error(
        "The Bland API may be experiencing high traffic. Try again in a moment."
      );
    } else if (error.response) {
      // The server responded with a non-2xx status code.
      console.error(
        `Error: API returned status code ${error.response.status}.`
      );
      console.error(
        `Response: ${JSON.stringify(error.response.data, null, 2)}`
      );
    } else {
      // Something else went wrong (network error, etc.).
      console.error(`Error: ${error.message}`);
    }
    process.exit(1);
  }

  // -------------------------------------------------------------------------
  // What happens during the call
  // -------------------------------------------------------------------------

  console.log("What to expect:");
  console.log(
    "  1. The agent will greet you using the persona's first_sentence."
  );
  console.log("  2. The agent speaks with the persona's selected voice.");
  console.log(
    "  3. The agent follows the persona's prompt and personality rules."
  );
  console.log(
    "  4. Background audio (if configured) plays during the call."
  );
  console.log(
    "  5. After the call, the analysis_schema fields are populated"
  );
  console.log("     automatically based on the conversation.");
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

sendCallWithPersona();
