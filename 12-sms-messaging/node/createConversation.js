/**
 * Bland AI - Create an AI-Powered SMS Conversation (Node.js)
 *
 * This script creates an autonomous AI SMS conversation using the Bland AI API.
 * Once created, the AI agent will send the initial message and then handle all
 * follow-up replies automatically, following the prompt you define.
 *
 * Use case: A dental office sends appointment follow-up texts to patients.
 * The AI agent confirms the appointment, answers questions about preparation,
 * and handles rescheduling requests.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key and phone numbers.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node createConversation.js
 *
 * The script will:
 *    - Create a new AI-powered SMS conversation
 *    - Print the conversation ID for tracking
 *    - The AI agent will then manage the conversation autonomously
 *
 * Note: SMS messaging is an Enterprise feature. Your Bland phone number
 * must be configured for SMS, and US numbers require A2P 10DLC registration.
 *
 * Pricing: Each message costs $0.02 (both inbound and outbound).
 */

// Load environment variables from the .env file in this directory.
// This keeps your API key and phone numbers out of source control.
require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

// The phone number to send SMS from. This must be a Bland phone number
// that has been configured for SMS in your Bland dashboard.
const FROM_NUMBER = process.env.FROM_NUMBER;

// The recipient's phone number in E.164 format (e.g., +15551234567).
// This is the person who will receive the AI-driven text conversation.
const TO_NUMBER = process.env.TO_NUMBER;

// The Bland API base URL. All SMS endpoints are under /v1/sms.
const BASE_URL = "https://api.bland.ai/v1";

// ---------------------------------------------------------------------------
// Validate configuration
// ---------------------------------------------------------------------------

if (!API_KEY) {
  console.error("Error: BLAND_API_KEY is not set.");
  console.error("Copy .env.example to .env and add your API key.");
  process.exit(1);
}

if (!FROM_NUMBER) {
  console.error("Error: FROM_NUMBER is not set.");
  console.error(
    "Add your SMS-configured Bland phone number to .env (e.g., +15551234567)."
  );
  process.exit(1);
}

if (!TO_NUMBER) {
  console.error("Error: TO_NUMBER is not set.");
  console.error(
    "Add the recipient's phone number in E.164 format to .env (e.g., +15551234567)."
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Define the AI agent prompt
// ---------------------------------------------------------------------------

// The "prompt" tells the AI agent how to behave throughout the SMS conversation.
// This is similar to the "task" parameter for voice calls, but optimized for
// text messaging. The agent will follow these instructions for every message
// it sends and every reply it processes.
//
// Tips for writing SMS prompts:
//   - Keep responses concise. Text messages should be short and scannable.
//   - Avoid filler phrases like "uh-huh" or "got it" that feel unnatural in text.
//   - Be specific about what information to collect and what actions to take.
//   - Define a clear end state so the agent knows when the conversation is done.
//   - Consider that replies may be delayed by minutes, hours, or even days.

const AGENT_PROMPT = `You are a friendly appointment follow-up assistant for Sunrise Dental.
Your name is Sam. You are texting a patient to confirm their upcoming dental appointment.

Appointment details:
- Patient name: the person you are texting
- Appointment date: Tomorrow at 10:00 AM
- Location: Sunrise Dental, 456 Oak Avenue, Suite 200
- Doctor: Dr. Martinez
- Type: Routine cleaning and checkup

Your goals:
1. Confirm the appointment. Ask the patient to reply "yes" to confirm or let you know if they need to reschedule.
2. If they confirm, remind them of the preparation instructions (listed below).
3. If they want to reschedule, ask for their preferred date and time, then let them know someone from the office will call to finalize.
4. Answer any questions they have about the appointment.

Preparation instructions to share when the patient confirms:
- Please arrive 10 minutes early to complete any paperwork.
- Brush and floss before your visit.
- Bring your insurance card and a photo ID.
- If you are taking any new medications, let us know when you arrive.

Important guidelines:
- Keep your messages short and friendly. One to three sentences per message is ideal for texting.
- Use a warm, professional tone. You represent a dental office, not a chatbot.
- Do not use medical jargon. Keep language simple and clear.
- If the patient has a question you cannot answer (like specific treatment costs or insurance coverage), let them know the office will follow up with details.
- Once the appointment is confirmed and instructions are shared, thank the patient and end the conversation.
- If the patient asks to cancel entirely, express understanding and let them know the office will reach out to reschedule when they are ready.

Example opening message: "Hi! This is Sam from Sunrise Dental. Just a friendly reminder that you have an appointment tomorrow at 10:00 AM with Dr. Martinez for a routine cleaning. Can you confirm you will be there?"`;

// ---------------------------------------------------------------------------
// Build the request payload
// ---------------------------------------------------------------------------

// The payload contains all the parameters for the Create SMS Conversation endpoint.
// Required fields: phone_number, from, prompt (or pathway_id).
// The AI agent will use these instructions to manage the entire conversation.

const payload = {
  // REQUIRED: The recipient's phone number in E.164 format.
  // The AI agent will send the initial message to this number and
  // handle all subsequent replies.
  phone_number: TO_NUMBER,

  // REQUIRED: Your Bland phone number that will appear as the sender.
  // This number must be SMS-configured in your Bland dashboard.
  from: FROM_NUMBER,

  // REQUIRED (unless using pathway_id): The instructions for the AI agent.
  // This defines the agent's personality, goals, and behavior for the
  // entire conversation. The agent will reference this prompt for every
  // message it sends and every reply it processes.
  prompt: AGENT_PROMPT,

  // OPTIONAL: Use a pathway instead of a prompt for conversation logic.
  // Pathways let you build visual conversation flows in the Bland dashboard.
  // If you set pathway_id, the agent follows the pathway instead of the prompt.
  // Note: When using a pathway, backchanneling phrases are automatically
  // stripped from responses to keep text messages clean and natural.
  // pathway_id: "your-pathway-id-here",

  // OPTIONAL: Pin the conversation to a specific version of the pathway.
  // This is useful if you have published multiple versions and want to
  // ensure this conversation uses a particular one.
  // pathway_version: 1,

  // OPTIONAL: Start the conversation at a specific node in the pathway.
  // By default, the conversation starts at the pathway's entry node.
  // Use this to skip ahead to a particular step in the flow.
  // node_id: "specific-node-id-here",
};

// ---------------------------------------------------------------------------
// Create the SMS conversation
// ---------------------------------------------------------------------------

async function createConversation() {
  console.log("Creating AI-powered SMS conversation...");
  console.log(`From: ${FROM_NUMBER}`);
  console.log(`To: ${TO_NUMBER}`);
  console.log();

  try {
    // Make the POST request to the Create SMS Conversation endpoint.
    // This creates the conversation and sends the first message immediately.
    // The AI agent will then handle all follow-up replies autonomously.
    const response = await axios.post(`${BASE_URL}/sms/create`, payload, {
      headers: {
        Authorization: API_KEY,
        "Content-Type": "application/json",
      },
      timeout: 30000, // 30-second timeout for the HTTP request itself
    });

    const data = response.data;

    console.log("SMS conversation created successfully!");
    console.log();
    console.log("Response from API:");
    console.log(JSON.stringify(data, null, 2));
    console.log();
    console.log(`The AI agent has sent the initial message to ${TO_NUMBER}.`);
    console.log("The agent will now handle all replies autonomously,");
    console.log("following the prompt instructions you provided.");
    console.log();
    console.log("To view this conversation later, run:");
    console.log("  node listConversations.js");
    console.log();
    console.log(
      "Or check the SMS section in the Bland dashboard at https://app.bland.ai"
    );
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

      // Provide specific guidance for common error codes.
      if (error.response.status === 401) {
        console.error();
        console.error("This usually means your API key is invalid or missing.");
      } else if (error.response.status === 400) {
        console.error();
        console.error("This usually means one of the parameters is invalid.");
        console.error("Check that your phone numbers are in E.164 format");
        console.error("and that your FROM_NUMBER is SMS-configured.");
      } else if (error.response.status === 403) {
        console.error();
        console.error("SMS may not be enabled on your plan.");
        console.error(
          "SMS is an Enterprise feature. Contact Bland support to enable it."
        );
      }
    } else {
      // Some other unexpected error.
      console.error(`Error: ${error.message}`);
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

createConversation();
