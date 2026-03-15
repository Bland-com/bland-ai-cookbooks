/**
 * Bland AI - Send an SMS Message (Node.js)
 *
 * This script sends a single SMS text message using the Bland AI API.
 * It demonstrates the simplest SMS operation: sending a one-off message
 * from your Bland phone number to a recipient.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key and phone numbers.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node sendSms.js
 *
 * The script will:
 *    - Send a text message to the specified recipient
 *    - Print the API response showing the delivery status
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
// It typically starts with "sk-".
const API_KEY = process.env.BLAND_API_KEY;

// The phone number to send the SMS from. This must be a Bland phone number
// that has been configured for SMS in your Bland dashboard.
const FROM_NUMBER = process.env.FROM_NUMBER;

// The recipient's phone number in E.164 format (e.g., +15551234567).
// This is the person who will receive your text message.
const TO_NUMBER = process.env.TO_NUMBER;

// The Bland API base URL. All SMS endpoints are under /v1/sms.
const BASE_URL = "https://api.bland.ai/v1";

// ---------------------------------------------------------------------------
// Validate configuration
// ---------------------------------------------------------------------------

// Make sure all required environment variables are present before
// making any API calls. This prevents confusing errors later.

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
// Define the message content
// ---------------------------------------------------------------------------

// This is the text message that will be sent to the recipient.
// Keep it clear and concise. Standard SMS messages are limited to
// 160 characters (GSM-7 encoding) or 70 characters (Unicode).
// Longer messages are automatically split into multiple segments
// but still count as a single API message for billing purposes.

const MESSAGE =
  "Hi! This is a test message from Bland AI. " +
  "Your SMS integration is working correctly. " +
  "Reply to this message to test two-way communication.";

// ---------------------------------------------------------------------------
// Build the request payload
// ---------------------------------------------------------------------------

// The payload contains all the parameters for the Send SMS endpoint.
// Required fields: phone_number, from, message.
// Optional fields: pathway_id, wait.

const payload = {
  // REQUIRED: The recipient's phone number in E.164 format.
  // This is the person who will receive the text message.
  phone_number: TO_NUMBER,

  // REQUIRED: Your Bland phone number that will appear as the sender.
  // This number must be SMS-configured in your Bland dashboard.
  // It can be the same number you use for voice calls.
  from: FROM_NUMBER,

  // REQUIRED: The actual text content of the message.
  // This is what the recipient will see on their phone.
  message: MESSAGE,

  // OPTIONAL: Attach a pathway to drive follow-up conversation logic.
  // If the recipient replies, the pathway will handle the response
  // automatically using your defined conversation flow.
  // Uncomment the line below and replace with your pathway ID to use this.
  // pathway_id: "your-pathway-id-here",

  // OPTIONAL: If true, the API call will wait for the recipient to reply
  // before returning a response. This is useful for synchronous workflows
  // where you need the reply immediately, but it will block until a
  // response is received (or the request times out).
  // wait: false,
};

// ---------------------------------------------------------------------------
// Send the SMS
// ---------------------------------------------------------------------------

async function sendSms() {
  console.log(`Sending SMS to ${TO_NUMBER}...`);
  console.log(`From: ${FROM_NUMBER}`);
  console.log(`Message: ${MESSAGE}`);
  console.log();

  try {
    // Make the POST request to the Send SMS endpoint.
    // The Authorization header uses your API key directly (no "Bearer" prefix).
    // This sends the text message immediately.
    const response = await axios.post(`${BASE_URL}/sms/send`, payload, {
      headers: {
        Authorization: API_KEY,
        "Content-Type": "application/json",
      },
      timeout: 30000, // 30-second timeout for the HTTP request itself
    });

    const data = response.data;

    // Print the full response so you can see all the fields returned.
    console.log("SMS sent successfully!");
    console.log();
    console.log("Response from API:");
    console.log(JSON.stringify(data, null, 2));
    console.log();
    console.log(
      "The recipient should receive the message within a few seconds."
    );
    console.log(
      "Each message costs $0.02. Check your Bland dashboard for billing details."
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
        console.error("Check that BLAND_API_KEY is correct in your .env file.");
      } else if (error.response.status === 400) {
        console.error();
        console.error("This usually means one of the parameters is invalid.");
        console.error("Check that your phone numbers are in E.164 format");
        console.error("and that your FROM_NUMBER is SMS-configured.");
      } else if (error.response.status === 403) {
        console.error();
        console.error("This may mean SMS is not enabled on your plan.");
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

sendSms();
