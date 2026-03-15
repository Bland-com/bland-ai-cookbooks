/**
 * createWidget.js
 *
 * Creates a Bland AI web chat widget via the API. The widget can be embedded
 * on any website to give visitors an AI-powered chat assistant.
 *
 * Usage:
 *    1. Copy .env.example to .env and add your Bland API key.
 *    2. Run: node createWidget.js
 *    3. Copy the widget_id from the output and use it in your HTML page.
 *
 * Dependencies:
 *    npm install axios dotenv
 */

// ---------------------------------------------------------------------------
// Load environment variables from the .env file in the same directory.
// This keeps your API key out of source control.
// ---------------------------------------------------------------------------
require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Read the API key from the environment. This key authenticates every request
// to the Bland API. You can find yours at https://app.bland.ai under
// Settings > API Keys.
// ---------------------------------------------------------------------------
const BLAND_API_KEY = process.env.BLAND_API_KEY;

// Validate that the API key is present before making any requests.
if (!BLAND_API_KEY) {
  console.error(
    "Error: BLAND_API_KEY is not set.\n" +
      "Copy .env.example to .env and add your API key."
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// Bland API endpoint for creating a web chat widget.
// ---------------------------------------------------------------------------
const CREATE_WIDGET_URL = "https://api.bland.ai/v1/widget";

// ---------------------------------------------------------------------------
// Widget configuration payload.
//
// This defines how the chat agent behaves when visitors interact with it.
// You can customize every field below to match your use case.
// ---------------------------------------------------------------------------
const widgetConfig = {
  // -------------------------------------------------------------------------
  // prompt (string, required)
  //
  // The system prompt that defines the agent's personality, knowledge, and
  // behavior. This is the most important field. Write it as if you are
  // training a new support agent: tell it who it is, what it knows, how
  // it should respond, and what it should avoid.
  //
  // You can include dynamic variables using {{variable_name}} syntax.
  // These variables are filled in at runtime from the request_data object
  // passed in window.blandSettings on your HTML page.
  // -------------------------------------------------------------------------
  prompt: [
    "You are a friendly and knowledgeable customer support agent for",
    "NovaCRM, a modern CRM platform for growing businesses.",
    "",
    "Your name is Nova. You help visitors understand NovaCRM's features,",
    "pricing, and integrations. You can answer questions about:",
    "- Plans and pricing (Starter at $19/mo, Pro at $49/mo, Enterprise",
    "  at $99/mo)",
    "- Key features (contact management, pipeline tracking, email",
    "  automation, reporting, API access)",
    "- Integrations (Slack, Gmail, Salesforce import, Zapier, webhooks)",
    "- Getting started and onboarding",
    "",
    "If the visitor asks something you cannot answer, offer to connect",
    "them with a human team member.",
    "",
    "If the visitor provides their name via request_data, greet them by",
    "name. For example: 'Hi {{first_name}}, welcome to NovaCRM!'",
    "",
    "Keep responses concise, helpful, and friendly. Use short paragraphs.",
  ].join("\n"),

  // -------------------------------------------------------------------------
  // voice (string, optional)
  //
  // The voice the agent uses if voice mode is enabled on the widget. This
  // uses the same voice options available for phone calls.
  // Common options: "mason", "maya", "ryan", "tina", "josh", "florian",
  // "derek", "june", "nat", "paige".
  // -------------------------------------------------------------------------
  voice: "maya",

  // -------------------------------------------------------------------------
  // first_sentence (string, optional)
  //
  // The greeting message the agent sends as soon as a visitor opens the
  // chat. If omitted, the agent generates its own greeting based on the
  // prompt.
  // -------------------------------------------------------------------------
  first_sentence:
    "Hey there! I'm Nova, your NovaCRM assistant. How can I help you today?",

  // -------------------------------------------------------------------------
  // model (string, optional)
  //
  // Which AI model powers the agent.
  // - "base": Full feature support, recommended for most use cases.
  // - "turbo": Lower latency but may not support all features.
  // -------------------------------------------------------------------------
  model: "base",

  // -------------------------------------------------------------------------
  // temperature (float, optional)
  //
  // Controls the randomness of the agent's responses.
  // - 0.0: Deterministic, always picks the most likely response.
  // - 1.0: Maximum creativity and variation.
  // - 0.7: A good balance for conversational agents.
  // -------------------------------------------------------------------------
  temperature: 0.7,

  // -------------------------------------------------------------------------
  // tools (array, optional)
  //
  // Custom tools the agent can invoke during the conversation. Each tool
  // is an API call the agent can trigger when it determines the visitor
  // needs information that requires a live lookup.
  //
  // Below is an example tool that checks pricing for a given plan. In a
  // real application, this would call your own backend API.
  // -------------------------------------------------------------------------
  tools: [
    {
      // A human-readable name for the tool.
      name: "check_plan_details",

      // A description that helps the AI decide when to use this tool.
      description:
        "Retrieves detailed information about a specific NovaCRM " +
        "pricing plan, including features, limits, and current promotions.",

      // The URL to call when the tool is triggered.
      url: "https://your-api.example.com/plans/details",

      // The HTTP method to use.
      method: "GET",

      // The parameters the agent should collect before calling the tool.
      parameters: {
        type: "object",
        properties: {
          plan_name: {
            type: "string",
            description:
              "The name of the plan to look up " +
              "(starter, pro, or enterprise).",
          },
        },
        required: ["plan_name"],
      },
    },
  ],
};

// ---------------------------------------------------------------------------
// Make the API request to create the widget.
// ---------------------------------------------------------------------------
async function createWidget() {
  console.log("Creating Bland AI web chat widget...");
  console.log();

  try {
    // Send a POST request to the Bland API with the widget configuration.
    // The Authorization header uses the raw API key (no "Bearer" prefix).
    const response = await axios.post(CREATE_WIDGET_URL, widgetConfig, {
      headers: {
        Authorization: BLAND_API_KEY,
        "Content-Type": "application/json",
      },
    });

    // Extract the response data.
    const data = response.data;

    // -----------------------------------------------------------------------
    // Print the results. The most important field is widget_id, which you
    // will use to embed the widget on your website.
    // -----------------------------------------------------------------------
    console.log("Widget created successfully!");
    console.log();
    console.log(`  Widget ID: ${data.widget_id || "N/A"}`);
    console.log();
    console.log("Full API response:");
    console.log(JSON.stringify(data, null, 2));
    console.log();
    console.log("Next steps:");
    console.log("  1. Copy the widget_id above.");
    console.log("  2. Open index.html (in the parent directory).");
    console.log("  3. Replace YOUR_WIDGET_ID with your actual widget ID.");
    console.log("  4. Open index.html in a browser to see the widget in action.");
  } catch (error) {
    // -----------------------------------------------------------------------
    // Handle errors from the API or network.
    // -----------------------------------------------------------------------
    if (error.response) {
      // The server responded with an error status code (4xx, 5xx).
      // Common causes:
      //   401: Invalid API key.
      //   400: Malformed request body.
      //   429: Rate limit exceeded.
      console.error(`HTTP error: ${error.response.status}`);
      console.error(`Response body: ${JSON.stringify(error.response.data)}`);
    } else if (error.request) {
      // The request was made but no response was received.
      // This usually means a network connectivity issue.
      console.error("Connection error: could not reach the Bland API.");
      console.error("Check your internet connection and try again.");
    } else {
      // Something else went wrong while setting up the request.
      console.error(`An unexpected error occurred: ${error.message}`);
    }

    process.exit(1);
  }
}

// Run the main function.
createWidget();
