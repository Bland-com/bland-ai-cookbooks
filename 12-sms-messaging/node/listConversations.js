/**
 * Bland AI - List SMS Conversations (Node.js)
 *
 * This script retrieves all SMS conversations from your Bland AI account
 * and displays them in a readable format with conversation IDs, phone numbers,
 * message counts, and statuses.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node listConversations.js
 *
 * The script will:
 *    - Fetch all SMS conversations from the API
 *    - Display each conversation's key details in a formatted table
 *    - Show the total number of conversations
 *
 * Note: SMS messaging is an Enterprise feature. Your account must have
 * SMS enabled to use this endpoint.
 */

// Load environment variables from the .env file in this directory.
require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

// The Bland API base URL. All SMS endpoints are under /v1/sms.
const BASE_URL = "https://api.bland.ai/v1";

// ---------------------------------------------------------------------------
// Validate configuration
// ---------------------------------------------------------------------------

// Only the API key is needed for listing conversations. No phone numbers
// are required since we are just reading data.

if (!API_KEY) {
  console.error("Error: BLAND_API_KEY is not set.");
  console.error("Copy .env.example to .env and add your API key.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Fetch and display SMS conversations
// ---------------------------------------------------------------------------

async function listConversations() {
  console.log("Fetching SMS conversations...");
  console.log();

  try {
    // Make the GET request to the List Conversations endpoint.
    // This returns all SMS conversations associated with your account.
    // The Authorization header uses your API key directly (no "Bearer" prefix).
    const response = await axios.get(`${BASE_URL}/sms/conversations`, {
      headers: {
        Authorization: API_KEY,
      },
      timeout: 30000, // 30-second timeout for the HTTP request itself
    });

    const data = response.data;

    // -----------------------------------------------------------------------
    // Parse the response
    // -----------------------------------------------------------------------

    // Extract the conversations list from the response.
    // The API may return the list directly as an array, or nested
    // under a "conversations" or "data" key. We handle all cases.
    let conversations;

    if (Array.isArray(data)) {
      // The response is a list of conversations directly.
      conversations = data;
    } else if (typeof data === "object" && data !== null) {
      // The response is an object. Look for common keys that hold the list.
      conversations = data.conversations || data.data || [];
      if (!Array.isArray(conversations)) {
        // If neither key holds an array, treat the whole object as one item.
        conversations = [data];
      }
    } else {
      console.log("Unexpected response format:");
      console.log(JSON.stringify(data, null, 2));
      process.exit(1);
    }

    // -----------------------------------------------------------------------
    // Check for empty results
    // -----------------------------------------------------------------------

    if (conversations.length === 0) {
      console.log("No SMS conversations found.");
      console.log();
      console.log("To create your first conversation, run:");
      console.log("  node createConversation.js");
      console.log();
      console.log("Or send a message with:");
      console.log("  node sendSms.js");
      return;
    }

    // -----------------------------------------------------------------------
    // Display the conversations in a formatted table
    // -----------------------------------------------------------------------

    console.log(`Found ${conversations.length} conversation(s):`);
    console.log();

    // Print the table header.
    // We use padEnd() to create fixed-width columns for readable output.
    const header =
      "Conversation ID".padEnd(40) +
      "From".padEnd(16) +
      "To".padEnd(16) +
      "Messages".padEnd(10) +
      "Status".padEnd(12);
    console.log(header);
    console.log("-".repeat(94));

    // Iterate through each conversation and display its details.
    for (const convo of conversations) {
      // The unique identifier for this conversation. Use this to fetch
      // full conversation details or analyze the conversation.
      const convoId = convo.id || convo.conversation_id || "N/A";

      // The Bland phone number that sent the messages.
      const fromNumber = convo.from || convo.from_number || "N/A";

      // The recipient's phone number.
      const toNumber = convo.to || convo.phone_number || "N/A";

      // The total number of messages exchanged in this conversation.
      // This includes both sent and received messages. The "messages"
      // field may be the count directly or the actual array of messages.
      let messageCount = convo.message_count || convo.messages || "N/A";
      if (Array.isArray(messageCount)) {
        // If "messages" is the actual message array, use its length.
        messageCount = messageCount.length;
      }

      // The current status of the conversation (e.g., "active", "completed").
      const status = convo.status || "N/A";

      // Print the conversation row with fixed-width columns.
      const row =
        String(convoId).substring(0, 38).padEnd(40) +
        String(fromNumber).substring(0, 14).padEnd(16) +
        String(toNumber).substring(0, 14).padEnd(16) +
        String(messageCount).padEnd(10) +
        String(status).substring(0, 10).padEnd(12);
      console.log(row);
    }

    // Print a summary footer with helpful next steps.
    console.log();
    console.log(`Total conversations: ${conversations.length}`);
    console.log();
    console.log("To view full details for a specific conversation,");
    console.log("use the conversation ID with the Get Conversation endpoint:");
    console.log(
      "  GET https://api.bland.ai/v1/sms/conversations/<conversation_id>"
    );
    console.log();
    console.log("To analyze a conversation, use the Analyze endpoint:");
    console.log("  POST https://api.bland.ai/v1/sms/analyze");
    console.log(
      '  Body: { "conversation_id": "<id>", "goal": "...", "questions": [...] }'
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

      if (error.response.status === 401) {
        console.error();
        console.error("This usually means your API key is invalid or missing.");
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

listConversations();
