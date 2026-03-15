/**
 * authorizeSession.js
 *
 * Authorizes a session for a Bland AI Web Agent, returning a single-use
 * token that the browser can use to start a voice conversation.
 *
 * Each token can only be used once. After a conversation starts with a
 * given token, that token is invalidated. Call this endpoint every time
 * a user wants to start a new conversation.
 *
 * Usage:
 *   1. Make sure .env contains both BLAND_API_KEY and BLAND_AGENT_ID.
 *   2. Run: node authorizeSession.js
 *   3. The script prints the session token that the frontend can use.
 *
 * Dependencies:
 *   npm install axios dotenv
 */

const axios = require("axios");
const dotenv = require("dotenv");

// ---------------------------------------------------------------------------
// 1. Load environment variables from the .env file.
// ---------------------------------------------------------------------------
dotenv.config();

// Your Bland API key. Used to authenticate the authorization request.
// This key must stay on the server and never be sent to the browser.
const BLAND_API_KEY = process.env.BLAND_API_KEY;

// The agent ID returned when you created the web agent (see createAgent.js).
// This identifies which agent configuration to use for the session.
const BLAND_AGENT_ID = process.env.BLAND_AGENT_ID;

// Validate that both required environment variables are present.
if (!BLAND_API_KEY) {
  console.error(
    "Error: BLAND_API_KEY is not set.\n" +
      "Copy .env.example to .env and add your API key."
  );
  process.exit(1);
}

if (!BLAND_AGENT_ID) {
  console.error(
    "Error: BLAND_AGENT_ID is not set.\n" +
      "Run createAgent.js first to create an agent, then add the " +
      "agent_id to your .env file."
  );
  process.exit(1);
}

// ---------------------------------------------------------------------------
// 2. Build the authorization endpoint URL.
//    The agent_id is part of the URL path.
// ---------------------------------------------------------------------------
const AUTHORIZE_URL = `https://api.bland.ai/v1/agents/${BLAND_AGENT_ID}/authorize`;

// ---------------------------------------------------------------------------
// 3. Build the request body.
//    The request_data field lets you pass dynamic variables into the
//    conversation. These values replace {{variable_name}} placeholders
//    in the agent's prompt.
//
//    For example, if your agent prompt says "Hello {{name}}", and you pass
//    { name: "Sarah" } here, the agent will say "Hello Sarah".
// ---------------------------------------------------------------------------
const requestBody = {
  // request_data (object, optional):
  // Key-value pairs that get injected into the agent prompt as template
  // variables. Each key becomes available as {{key}} in the prompt.
  // Common uses:
  //   - User's name for personalized greetings
  //   - Account type for tailored responses
  //   - Order IDs or reference numbers for context
  request_data: {
    name: "Sarah",
  },
};

// ---------------------------------------------------------------------------
// 4. Send the authorization request and handle the response.
// ---------------------------------------------------------------------------
async function authorizeSession() {
  console.log("Authorizing session...");
  console.log(`Agent ID: ${BLAND_AGENT_ID}`);
  console.log(`Endpoint: ${AUTHORIZE_URL}`);
  console.log();

  try {
    // Make the POST request to authorize a new session.
    // Headers:
    //   - Authorization: Your raw API key (no "Bearer" prefix needed)
    //   - Content-Type: application/json for the JSON body
    const response = await axios.post(AUTHORIZE_URL, requestBody, {
      headers: {
        Authorization: BLAND_API_KEY,
        "Content-Type": "application/json",
      },
    });

    const data = response.data;

    // A successful response includes a "token" field containing the
    // single-use session token, and a "status" of "success".
    if (data.status === "success") {
      const token = data.token;

      console.log("Session authorized successfully!");
      console.log(`Session Token: ${token}`);
      console.log();
      console.log("This token is single-use. It can only start one conversation.");
      console.log("Pass this token to BlandWebClient in the browser to begin.");
      console.log();
      console.log("Example (JavaScript):");
      console.log(
        `  const client = new BlandWebClient("${BLAND_AGENT_ID}", "${token}");`
      );
      console.log('  await client.initConversation({ sampleRate: 44100 });');
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
authorizeSession();
