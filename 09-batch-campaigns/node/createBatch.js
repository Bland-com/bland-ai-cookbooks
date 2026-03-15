/**
 * Bland AI - Create a Batch Campaign (Node.js)
 *
 * This script reads a CSV file of patient records and submits them as a batch
 * campaign to the Bland AI API. Each row in the CSV becomes a personalized
 * outbound call. A shared "global" configuration provides the prompt template,
 * voice, and other defaults that apply to every call.
 *
 * Use case: A dental office calling patients to remind them of upcoming
 * appointments. Each call is personalized with the patient's name, appointment
 * date and time, dentist name, and service type.
 *
 * Usage:
 *     1. Copy .env.example to .env and fill in your API key.
 *     2. Install dependencies: npm install axios dotenv
 *     3. (Optional) Edit sample_leads.csv with your own phone numbers for testing.
 *     4. Run: node createBatch.js
 *
 * The script will:
 *     - Read the CSV file
 *     - Build a call_objects array with one entry per row
 *     - Attach a global configuration with the prompt template
 *     - Submit the batch to the Bland API
 *     - Print the batch_id for monitoring
 */

const fs = require("fs");
const path = require("path");
const axios = require("axios");

// Load environment variables from the .env file in this directory.
// This keeps your API key out of source control.
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

// Path to the CSV file containing patient records.
// Default is "../python/sample_leads.csv" (shared with the Python examples).
const CSV_FILE_PATH = process.env.CSV_FILE_PATH || "../python/sample_leads.csv";

// (Optional) Webhook URL for receiving batch lifecycle status updates.
// If set, Bland will POST to this URL as the batch moves through each stage.
const STATUS_WEBHOOK = process.env.STATUS_WEBHOOK || "";

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
// CSV parsing
// ---------------------------------------------------------------------------

/**
 * Parses a CSV string into an array of objects.
 * Each object uses the header row values as keys.
 * This is a lightweight parser that handles basic CSV format
 * without requiring an external library.
 *
 * @param {string} csvText - The raw CSV file contents.
 * @returns {Array<Object>} Array of row objects with header-based keys.
 */
function parseCSV(csvText) {
  // Split the CSV text into individual lines, filtering out empty lines.
  const lines = csvText
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  if (lines.length < 2) {
    // A valid CSV needs at least a header row and one data row.
    console.error("Error: CSV file must have a header row and at least one data row.");
    process.exit(1);
  }

  // The first line contains the column headers.
  const headers = lines[0].split(",").map((h) => h.trim());

  // Validate that the required "phone_number" column exists.
  if (!headers.includes("phone_number")) {
    console.error('Error: CSV file must have a "phone_number" column.');
    console.error("Found columns: " + headers.join(", "));
    process.exit(1);
  }

  // Parse each subsequent line into an object using the headers as keys.
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(",").map((v) => v.trim());
    const row = {};
    headers.forEach((header, index) => {
      row[header] = values[index] || "";
    });
    rows.push(row);
  }

  return rows;
}

// ---------------------------------------------------------------------------
// Read the CSV file
// ---------------------------------------------------------------------------

// Resolve the CSV path relative to this script's directory.
// This ensures the script works regardless of where it is called from.
const csvPath = path.resolve(__dirname, CSV_FILE_PATH);

if (!fs.existsSync(csvPath)) {
  console.error("Error: CSV file not found at '" + csvPath + "'.");
  console.error("Make sure the file exists or update CSV_FILE_PATH in your .env file.");
  process.exit(1);
}

console.log("Reading CSV file: " + csvPath);
console.log();

// Read and parse the CSV file.
const csvText = fs.readFileSync(csvPath, "utf-8");
const leads = parseCSV(csvText);

console.log("Loaded " + leads.length + " contacts from CSV.");
console.log();

if (leads.length === 0) {
  console.error("Error: No valid contacts found in the CSV file.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Build call objects
// ---------------------------------------------------------------------------

// Transform each lead into a call object for the Bland AI Batches API.
// Each call object contains the phone number to dial and request_data
// with the personalized variables that will be interpolated into the prompt.
const callObjects = leads.map((lead) => {
  // Extract the phone number (required per-call field).
  const phoneNumber = lead.phone_number;

  // Build request_data from all columns except phone_number.
  // Each key-value pair becomes a template variable: {{key}} in the prompt.
  const requestData = {};
  Object.keys(lead).forEach((key) => {
    if (key !== "phone_number" && lead[key]) {
      requestData[key] = lead[key];
    }
  });

  return {
    // REQUIRED: The phone number to call for this specific contact.
    phone_number: phoneNumber,

    // OPTIONAL: Per-call request_data populated from CSV columns.
    // Each key-value pair here becomes a template variable.
    // For example, if the CSV has a "patient_name" column with value
    // "Sarah Johnson", then {{patient_name}} in the prompt will be
    // replaced with "Sarah Johnson" for this call.
    request_data: requestData,
  };
});

// ---------------------------------------------------------------------------
// Define the global configuration
// ---------------------------------------------------------------------------

// The global config contains settings that apply to every call in the batch.
// Think of this as the "template" that all calls share. Individual calls can
// override any of these settings in their call_entry.
//
// IMPORTANT: The global config MUST include either "task" or "pathway_id".
//            It CANNOT include "phone_number" (that is per-call only).

const globalConfig = {
  // REQUIRED (one of task or pathway_id): The prompt template for the agent.
  // Use {{variable_name}} syntax to reference CSV columns. These variables
  // are automatically populated from each row's request_data.
  task: [
    "You are a friendly, professional receptionist for Bright Smile Dental Clinic.",
    "You are calling {{patient_name}} to remind them about their upcoming dental appointment.",
    "",
    "Appointment details:",
    "- Date: {{appointment_date}}",
    "- Time: {{appointment_time}}",
    "- Dentist: {{dentist_name}}",
    "- Service: {{service_type}}",
    "",
    "Your goals:",
    "1. Greet the patient warmly by name.",
    "2. Confirm their appointment details (date, time, dentist, and service).",
    "3. Ask if they need to reschedule. If yes, let them know someone from the office",
    "   will call them back to find a new time.",
    "4. Remind them to arrive 10 minutes early and bring their insurance card.",
    "5. Ask if they have any questions.",
    "6. Thank them and end the call politely.",
    "",
    "Important guidelines:",
    "- Keep responses to one or two sentences at a time. Phone conversations should feel natural and concise.",
    "- If the patient wants to cancel entirely, express understanding and let them know they can",
    "  call back anytime to rebook.",
    "- If the patient asks medical questions, let them know the dentist will be happy to discuss",
    "  that during their visit.",
    "- Be warm and reassuring, especially if the patient seems nervous about their procedure.",
    "- If you reach voicemail, leave a brief, friendly reminder message with the appointment details.",
  ].join("\n"),

  // OPTIONAL: The exact first sentence the agent says when the call connects.
  // Using template variables here personalizes the greeting immediately.
  first_sentence:
    "Hi, is this {{patient_name}}? " +
    "This is Bright Smile Dental Clinic calling with a quick reminder about your upcoming appointment.",

  // OPTIONAL: The voice the agent uses for all calls in the batch.
  // Available voices: "mason", "maya", "ryan", "tina", "josh",
  //                   "florian", "derek", "june", "nat", "paige"
  voice: "maya",

  // OPTIONAL: Which model to use for generating responses.
  // "base"  - Full-featured model with all capabilities.
  // "turbo" - Lowest latency, but may lack some features.
  model: "base",

  // OPTIONAL: Maximum call length in minutes. For short reminder calls,
  // 5 minutes is usually plenty. This prevents runaway calls that could
  // consume excessive credits.
  max_duration: 5,

  // OPTIONAL: Whether to record calls. Useful for quality assurance.
  // When true, recording_url will be available in call details after completion.
  record: true,

  // OPTIONAL: Controls randomness in responses.
  // 0.0 = deterministic, 1.0 = most creative.
  // 0.7 is a good default for natural conversation.
  temperature: 0.7,

  // OPTIONAL: What to do when the call goes to voicemail.
  // "action" options: "hangup", "leave_message", "ignore"
  // For appointment reminders, leaving a voicemail is usually the best choice.
  voicemail: {
    action: "leave_message",
    message:
      "Hi {{patient_name}}, this is Bright Smile Dental Clinic. " +
      "We are calling to remind you about your {{service_type}} appointment " +
      "on {{appointment_date}} at {{appointment_time}} with {{dentist_name}}. " +
      "Please arrive 10 minutes early and bring your insurance card. " +
      "If you need to reschedule, please call us back. Thank you!",
  },

  // OPTIONAL: If true, the agent waits for the human to speak first.
  // For outbound reminder calls, you want the agent to speak first.
  wait_for_greeting: false,

  // OPTIONAL: Ambient background audio for realism.
  // Options: null, "office", "cafe", "restaurant", "none"
  background_track: "office",
};

// ---------------------------------------------------------------------------
// Submit the batch
// ---------------------------------------------------------------------------

/**
 * Submits the batch to the Bland AI API and handles the response.
 * This is wrapped in an async function because we use await for the HTTP call.
 */
async function submitBatch() {
  // Build the batch payload combining call objects with global config.
  const batchPayload = {
    // REQUIRED: Array of individual call entries. Each entry must have at least
    // a "phone_number". All other fields are optional and override the global
    // config for that specific call.
    call_objects: callObjects,

    // REQUIRED: Default settings applied to all calls unless overridden.
    // Must include "task" or "pathway_id". Cannot include "phone_number".
    global: globalConfig,
  };

  // Add the status webhook if one was configured.
  // The webhook receives POST requests as the batch moves through its lifecycle:
  // validating, dispatching, in_progress, completed (or failed).
  if (STATUS_WEBHOOK) {
    batchPayload.status_webhook = STATUS_WEBHOOK;
  }

  // Set the authorization header. Bland uses a simple API key in the
  // Authorization header (no "Bearer" prefix needed).
  const requestHeaders = {
    Authorization: API_KEY,
    "Content-Type": "application/json",
  };

  console.log("Submitting batch of " + callObjects.length + " calls to Bland API...");
  console.log();

  try {
    // Make the POST request to the Create Batch endpoint.
    const response = await axios.post(BASE_URL + "/batches", batchPayload, {
      headers: requestHeaders,
      timeout: 60000, // 60 seconds. Larger batches may take a moment to process.
    });

    const data = response.data;

    // The successful response has this structure:
    // { "data": { "batch_id": "uuid" }, "errors": null }
    if (data.data && data.data.batch_id) {
      const batchIdResult = data.data.batch_id;
      console.log("Batch successfully created!");
      console.log("Batch ID: " + batchIdResult);
      console.log();
      console.log("Total calls in batch: " + callObjects.length);
      console.log();
      console.log("To monitor this batch, run:");
      console.log("  node monitorBatch.js " + batchIdResult);
      console.log();
      console.log("To stop this batch, run:");
      console.log("  node stopBatch.js " + batchIdResult);

      if (STATUS_WEBHOOK) {
        console.log();
        console.log("Status webhook configured: " + STATUS_WEBHOOK);
        console.log("You will receive POST requests as the batch progresses.");
      }
    } else if (data.errors) {
      // The API returned validation errors.
      console.error("Batch creation failed with errors:");
      console.error(JSON.stringify(data.errors, null, 2));
      process.exit(1);
    } else {
      // Unexpected response format.
      console.error("Unexpected response from API:");
      console.error(JSON.stringify(data, null, 2));
      process.exit(1);
    }
  } catch (error) {
    // Handle different types of errors.
    if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API.");
      console.error("Check your internet connection and try again.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The request timed out.");
      console.error("The Bland API may be experiencing high traffic. Try again in a moment.");
    } else if (error.response) {
      // The server responded with an error status code (4xx, 5xx).
      console.error("Error: API returned status code " + error.response.status + ".");
      console.error("Response: " + JSON.stringify(error.response.data));
    } else {
      console.error("Error: " + error.message);
    }

    process.exit(1);
  }
}

// Run the main function.
submitBatch();
