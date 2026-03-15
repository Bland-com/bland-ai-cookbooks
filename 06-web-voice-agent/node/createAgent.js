/**
 * createAgent.js
 *
 * Creates a Bland AI Web Agent that can be used for browser-based voice
 * conversations. The agent is a persistent configuration, meaning you create
 * it once and then authorize individual sessions against it. Think of it
 * like a template for conversations.
 *
 * Usage:
 *   1. Copy .env.example to .env and fill in your Bland API key.
 *   2. Run: node createAgent.js
 *   3. Copy the agent_id from the output and save it in your .env as BLAND_AGENT_ID.
 *
 * Dependencies:
 *   npm install axios dotenv
 */

const axios = require("axios");
const dotenv = require("dotenv");

// ---------------------------------------------------------------------------
// 1. Load environment variables from the .env file in the same directory.
//    This keeps sensitive values like your API key out of source control.
// ---------------------------------------------------------------------------
dotenv.config();

// Read the API key from the environment. This key authenticates all requests
// to the Bland API. You can find it in your Bland dashboard under
// Settings > API Keys.
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
// 2. Define the Bland API endpoint for creating agents.
// ---------------------------------------------------------------------------
const CREATE_AGENT_URL = "https://api.bland.ai/v1/agents";

// ---------------------------------------------------------------------------
// 3. Build the agent configuration payload.
//    This defines everything about how the agent behaves during conversations.
// ---------------------------------------------------------------------------
const agentConfig = {
  // prompt (string, required):
  // The core instructions for your agent. This tells the AI who it is,
  // how it should behave, what it knows, and what it should do.
  // Write this as if you are briefing a new employee on their role.
  prompt: `You are a friendly and knowledgeable customer support assistant for Acme Corp, a software company that makes project management tools. Your name is Alex.

Your responsibilities:
- Answer questions about Acme Corp's products and pricing
- Help users troubleshoot common issues
- Collect feedback and feature requests
- Escalate complex technical issues by recommending the user email support@acme.com

Guidelines:
- Be conversational and warm, but stay professional
- Keep responses concise (1 to 3 sentences when possible)
- If you do not know the answer, say so honestly
- Never make up information about products or pricing

Pricing information:
- Free tier: Up to 5 users, basic features
- Pro tier: $12/user/month, advanced features and integrations
- Enterprise tier: Custom pricing, dedicated support and SLAs

If the user provides their name, greet them by name. You can access the user's name via the variable {{name}} if it was provided.`,

  // voice (string, optional, default "mason"):
  // Which voice the agent uses to speak. Each voice has a distinct tone
  // and personality. Try different voices to find the best fit for your brand.
  // Options include: "mason", "maya", "ryan", "tina", "josh", "florian",
  // "derek", "june", "nat", "paige"
  voice: "mason",

  // first_sentence (string, optional, max 200 characters):
  // The exact sentence the agent says at the start of every conversation.
  // If omitted, the agent generates its own greeting based on the prompt.
  // Keep it short and welcoming.
  first_sentence: "Hi there! Welcome to Acme Corp support. How can I help you today?",

  // language (string, optional, default "ENG"):
  // The language for the conversation. The agent will both listen and
  // respond in this language. Default is English.
  language: "ENG",

  // model (string, optional, default "base"):
  // Which AI model powers the agent.
  // - "base": Full feature support, reliable for most use cases
  // - "turbo": Lower latency (faster responses), but may lack some features
  // For most web agent use cases, "base" is recommended.
  model: "base",

  // interruption_threshold (number, optional, default 500):
  // Controls how patient the agent is before it starts responding,
  // measured in milliseconds. Lower values make the agent jump in faster
  // when there is a pause. Higher values let the user finish longer thoughts.
  // Recommended range: 50 to 200 for responsive web agents.
  interruption_threshold: 100,

  // max_duration (number, optional, default 30):
  // Maximum conversation length in minutes. The session automatically
  // ends after this duration. Set this based on your expected conversation
  // length to prevent runaway sessions.
  max_duration: 15,

  // keywords (string[], optional):
  // Words or phrases that the transcription engine should prioritize.
  // Use this for product names, technical terms, or brand-specific
  // vocabulary that might otherwise be misheard.
  keywords: ["Acme Corp", "Pro tier", "Enterprise"],

  // metadata (object, optional):
  // Custom key-value pairs attached to the agent for your own tracking.
  // These are returned in webhooks and call details, making it easy to
  // filter and organize conversations in your system.
  metadata: {
    department: "customer_support",
    version: "1.0",
  },

  // analysis_schema (object, optional):
  // Defines structured data that Bland extracts from each conversation
  // after it ends. This is useful for automatically capturing insights
  // without needing to parse the transcript yourself.
  analysis_schema: {
    topic:
      "string: The main topic the user asked about (e.g., pricing, troubleshooting, feedback)",
    sentiment:
      "string: The overall sentiment of the user (positive, neutral, or negative)",
    resolved: "boolean: Whether the user's question was fully answered",
    follow_up_needed:
      "boolean: Whether the user needs additional follow-up",
  },
};

// ---------------------------------------------------------------------------
// 4. Send the request to create the agent.
// ---------------------------------------------------------------------------
async function createAgent() {
  console.log("Creating web agent...");
  console.log(`Endpoint: ${CREATE_AGENT_URL}`);
  console.log();

  try {
    // Make the POST request with the agent configuration.
    // Headers:
    //   - Authorization: Your raw API key (no "Bearer" prefix needed)
    //   - Content-Type: Automatically set to application/json by axios
    const response = await axios.post(CREATE_AGENT_URL, agentConfig, {
      headers: {
        Authorization: BLAND_API_KEY,
        "Content-Type": "application/json",
      },
    });

    const data = response.data;

    // A successful response includes a "status" of "success" and the
    // full agent object with the agent_id you need for authorizing sessions.
    if (data.status === "success") {
      const agent = data.agent || {};
      const agentId = agent.agent_id;

      console.log("Agent created successfully!");
      console.log(`Agent ID: ${agentId}`);
      console.log(`Voice: ${agent.voice}`);
      console.log(`Model: ${agent.model}`);
      console.log();
      console.log("Next steps:");
      console.log(`  1. Add this to your .env file: BLAND_AGENT_ID=${agentId}`);
      console.log("  2. Run authorizeSession.js to get a session token");
      console.log("  3. Use the token with BlandWebClient in the browser");
    } else {
      console.log("Unexpected response format:");
      console.log(JSON.stringify(data, null, 2));
    }
  } catch (error) {
    // Axios wraps HTTP errors in an error object. Extract the useful details.
    if (error.response) {
      console.error(`Error: HTTP ${error.response.status}`);
      console.error(JSON.stringify(error.response.data, null, 2));
    } else {
      console.error("Error:", error.message);
    }
  }
}

// Run the function.
createAgent();
