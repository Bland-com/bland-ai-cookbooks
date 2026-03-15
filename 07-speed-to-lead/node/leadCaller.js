// Speed to Lead: Lead Caller - Node.js
//
// This module exports a callLead() function that takes lead data (name, phone,
// email, source, product interest) and immediately fires off a Bland AI
// outbound call to qualify the lead.
//
// The AI agent will:
//   - Greet the lead by name
//   - Reference what they were interested in
//   - Ask qualifying questions (budget, timeline, decision maker)
//   - Offer to transfer qualified leads to a live sales rep
//   - Leave a personalized voicemail if the lead does not answer
//
// Usage:
//   1. Copy .env.example to .env and add your credentials.
//   2. Run directly: node leadCaller.js
//      (This sends a test call using the sample lead data at the bottom.)
//   3. Or import and call from your own code:
//      const { callLead } = require("./leadCaller");
//      const result = await callLead("Jane Smith", "+15551234567",
//                                     "jane@example.com", "Website Form",
//                                     "Enterprise Plan");
//
// Dependencies:
//   npm install axios dotenv

const axios = require("axios");
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// All values come from the .env file. See .env.example for the full list.
// ---------------------------------------------------------------------------

// Your Bland AI API key. Find it at https://app.bland.ai under
// Settings > API Keys. It typically starts with "sk-".
const API_KEY = process.env.BLAND_API_KEY;

// The Bland AI endpoint for placing outbound calls.
const CALLS_URL = "https://api.bland.ai/v1/calls";

// The public URL where Bland will POST call results once the call finishes.
// This must be reachable from the internet. Use ngrok for local testing.
const WEBHOOK_URL =
  process.env.WEBHOOK_URL || "https://your-server.com/webhook/call-complete";

// Phone number for transferring qualified leads to a live sales rep.
const TRANSFER_NUMBER = process.env.TRANSFER_NUMBER || "+15559876543";

// Your company name, referenced in the prompt and voicemail message.
const COMPANY_NAME = process.env.COMPANY_NAME || "Acme Corp";

/**
 * Build the qualification prompt for the AI agent.
 *
 * This prompt uses dynamic variables (wrapped in double curly braces) that
 * Bland replaces at call time with the actual values from request_data.
 *
 * The prompt follows BANT qualification methodology:
 *   B - Budget: Do they have money to spend?
 *   A - Authority: Are they the decision maker?
 *   N - Need: What problem are they solving?
 *   T - Timeline: When do they want to act?
 *
 * @param {string} companyName - The name of your company.
 * @returns {string} The full prompt string for the AI agent.
 */
function buildQualificationPrompt(companyName) {
  return (
    `You are a friendly, professional sales development representative ` +
    `for ${companyName}. You are calling {{lead_name}} who just expressed ` +
    `interest in {{product_interest}} through {{lead_source}}.\n\n` +
    `Your goals on this call:\n` +
    `1. Greet them warmly by name and reference what they were looking at.\n` +
    `2. Confirm they are the right person and that now is a good time to talk.\n` +
    `3. Ask these qualifying questions naturally (do not read them like a list):\n` +
    `   - What problem are they trying to solve?\n` +
    `   - What is their timeline for making a decision?\n` +
    `   - Who else is involved in the decision?\n` +
    `   - Do they have a budget range in mind?\n` +
    `4. Based on their answers, determine if they are a qualified lead.\n` +
    `5. If they seem qualified and interested, offer to transfer them to a ` +
    `specialist right now, or offer to book a demo at a time that works for them.\n` +
    `6. If they are not qualified or not interested, thank them politely and ` +
    `let them know you will send a follow-up email with more information.\n\n` +
    `Important rules:\n` +
    `- Be conversational and natural. Do not sound like a robot reading a script.\n` +
    `- Do not ask all questions at once. Let the conversation flow naturally.\n` +
    `- If they seem busy, offer to call back at a better time.\n` +
    `- Never be pushy or aggressive. You are here to help, not to hard sell.\n` +
    `- If they ask a question you cannot answer, say you will have a specialist ` +
    `follow up with the answer.\n` +
    `- Keep the call concise. Aim for 3 to 5 minutes unless the lead wants ` +
    `to keep talking.\n` +
    `- Always be polite, even if the lead is not interested.\n\n` +
    `Their email on file is {{lead_email}}. You can reference this if needed ` +
    `to confirm identity or offer to send information.`
  );
}

/**
 * Build the voicemail message left if the lead does not answer.
 *
 * Personalized using dynamic variables from request_data.
 * Keep it short (under 30 seconds when spoken).
 *
 * @param {string} companyName - The name of your company.
 * @returns {string} The voicemail message string.
 */
function buildVoicemailMessage(companyName) {
  return (
    `Hi {{lead_name}}, this is Alex from ${companyName}. ` +
    `You recently expressed interest in {{product_interest}} and I wanted ` +
    `to connect with you personally. I will send you a follow-up email with ` +
    `some helpful information. If you would like to chat, you can call us ` +
    `back at this number anytime. Looking forward to connecting with you!`
  );
}

/**
 * Trigger an immediate Bland AI call to a new lead.
 *
 * Builds the full API payload with a personalized qualification prompt,
 * voicemail handling, transfer configuration, and dynamic variables,
 * then sends it to the Bland AI /v1/calls endpoint.
 *
 * @param {string} name     - The lead's full name (e.g., "Jane Smith").
 * @param {string} phone    - Phone number in E.164 format (e.g., "+15551234567").
 * @param {string} email    - The lead's email address.
 * @param {string} source   - Where the lead came from (e.g., "Website Form").
 * @param {string} interest - The product or service the lead is interested in.
 * @returns {Promise<object|null>} The Bland API response, or null on failure.
 */
async function callLead(name, phone, email, source, interest) {
  // Validate that the API key is set before making the request.
  if (!API_KEY) {
    console.error("Error: BLAND_API_KEY is not set.");
    console.error("Copy .env.example to .env and add your API key.");
    return null;
  }

  // Build the request headers. Bland uses the raw API key in the
  // Authorization header (no "Bearer" prefix).
  const headers = {
    Authorization: API_KEY,
    "Content-Type": "application/json",
  };

  // Build the full API payload.
  const payload = {
    // The lead's phone number in E.164 format.
    phone_number: phone,

    // The qualification prompt with dynamic variable placeholders.
    // Bland replaces {{lead_name}}, {{product_interest}}, etc. with
    // the values from request_data at call time.
    task: buildQualificationPrompt(COMPANY_NAME),

    // The first sentence the agent speaks when the call connects.
    // Personalizing this immediately shows the lead this is not spam.
    first_sentence:
      `Hi ${name}, this is Alex from ${COMPANY_NAME}. ` +
      `I saw you were just looking at our ${interest} options and ` +
      `wanted to personally reach out. Do you have a quick moment?`,

    // Voice selection. "mason" is a professional, friendly male voice.
    // Other options: "maya", "ryan", "tina", "josh", "florian", etc.
    voice: "mason",

    // AI model to use. "base" supports all features including transfers,
    // tools, and voicemail detection.
    model: "base",

    // Maximum call duration in minutes. 10 minutes is generous for a
    // qualification call. The call ends automatically after this.
    max_duration: 10,

    // Enable call recording for later review. The recording URL will
    // appear in the post-call webhook data.
    record: true,

    // Dynamic variables injected into the prompt. Any key here can be
    // referenced in the task prompt using {{key_name}} syntax.
    request_data: {
      lead_name: name,
      lead_email: email,
      lead_source: source,
      product_interest: interest,
    },

    // URL where Bland sends a POST with full call data (transcript,
    // summary, recording, duration, etc.) when the call finishes.
    webhook: WEBHOOK_URL,

    // Voicemail configuration. If the call goes to voicemail, the agent
    // leaves a personalized message instead of hanging up silently.
    voicemail: {
      action: "leave_message",
      message: buildVoicemailMessage(COMPANY_NAME),
    },

    // Default phone number for transferring qualified leads to a live rep.
    transfer_phone_number: TRANSFER_NUMBER,
  };

  // Log the outgoing request for debugging.
  console.log(`Calling lead: ${name} at ${phone}`);
  console.log(`Source: ${source}`);
  console.log(`Interest: ${interest}`);
  console.log(`Webhook URL: ${WEBHOOK_URL}`);
  console.log();

  try {
    // Send the POST request to the Bland API. The API responds
    // immediately with a call_id. The actual phone call is placed
    // asynchronously by Bland's infrastructure.
    const response = await axios.post(CALLS_URL, payload, { headers });
    const data = response.data;

    console.log("Call successfully queued!");
    console.log(`Call ID: ${data.call_id || "unknown"}`);
    console.log(`Status: ${data.status || "unknown"}`);
    console.log();
    console.log("The lead's phone will ring within seconds.");
    console.log("Post-call results will be sent to your webhook URL.");

    return data;
  } catch (error) {
    // Handle API errors and network failures.
    if (error.response) {
      // The API returned an error response (4xx or 5xx).
      console.error(`Error: Received status code ${error.response.status}`);
      console.error(JSON.stringify(error.response.data, null, 2));
      return error.response.data;
    } else if (error.request) {
      // The request was sent but no response was received (network error).
      console.error("Request failed: No response received from Bland API.");
      console.error(error.message);
    } else {
      // Something went wrong setting up the request.
      console.error("Request failed:", error.message);
    }
    return null;
  }
}

// Export the callLead function so webhookReceiver.js and other modules
// can import it.
module.exports = { callLead };

// ---------------------------------------------------------------------------
// Main: Run this file directly to send a test call.
// Replace the sample values below with real data for testing.
// ---------------------------------------------------------------------------
if (require.main === module) {
  // Sample lead data. Replace the phone number with your own so you
  // can answer the call and test the conversation.
  const testLead = {
    name: "Jane Smith",
    phone: "+15551234567",
    email: "jane@example.com",
    source: "Website Contact Form",
    interest: "Enterprise Plan",
  };

  console.log("============================================================");
  console.log("Speed to Lead: Sending test call");
  console.log("============================================================");
  console.log();

  callLead(
    testLead.name,
    testLead.phone,
    testLead.email,
    testLead.source,
    testLead.interest
  ).then((result) => {
    if (result) {
      console.log();
      console.log("Full API response:");
      console.log(JSON.stringify(result, null, 2));
    }
  });
}
