/**
 * server.js
 *
 * A complete Express server that:
 *   1. Serves the frontend HTML page (index.html) at the root URL
 *   2. Provides an /authorize endpoint that creates single-use session tokens
 *
 * This server acts as the secure backend for the web voice agent demo.
 * It keeps the Bland API key on the server side and only sends short-lived,
 * single-use session tokens to the browser.
 *
 * Usage:
 *   1. Make sure .env contains BLAND_API_KEY and BLAND_AGENT_ID.
 *   2. Run: node server.js
 *   3. Open http://localhost:3000 in your browser.
 *
 * Dependencies:
 *   npm install express axios dotenv cors
 */

const express = require("express");
const axios = require("axios");
const dotenv = require("dotenv");
const cors = require("cors");
const path = require("path");

// ---------------------------------------------------------------------------
// 1. Load environment variables from the .env file.
//    This keeps your API key and agent ID out of source control.
// ---------------------------------------------------------------------------
dotenv.config();

// Your Bland API key. This authenticates all requests to the Bland API.
// It must never be sent to the browser or exposed in frontend code.
const BLAND_API_KEY = process.env.BLAND_API_KEY;

// The agent ID returned when you created the web agent (see createAgent.js).
// This identifies which agent configuration to use for sessions.
const BLAND_AGENT_ID = process.env.BLAND_AGENT_ID;

// The port the server listens on. Defaults to 3000 if not set.
const PORT = process.env.PORT || 3000;

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
// 2. Create and configure the Express application.
// ---------------------------------------------------------------------------
const app = express();

// Enable CORS (Cross-Origin Resource Sharing) so the frontend can call the
// API from a different origin during development. In production, you should
// restrict this to your actual domain.
app.use(cors());

// Parse JSON request bodies. This is needed for the /authorize endpoint
// to read any user data sent from the frontend.
app.use(express.json());

// ---------------------------------------------------------------------------
// 3. Serve the frontend HTML page.
//    The index.html file lives one directory up from the node/ folder.
//    Serving it at "/" means opening http://localhost:3000 loads the demo.
// ---------------------------------------------------------------------------
app.get("/", (req, res) => {
  // Resolve the path to index.html relative to this server file.
  // The file is in the parent directory (06-web-voice-agent/index.html).
  const htmlPath = path.resolve(__dirname, "..", "index.html");
  res.sendFile(htmlPath);
});

// ---------------------------------------------------------------------------
// 4. Session authorization endpoint.
//    The frontend calls this to get a single-use session token before
//    starting a voice conversation. This endpoint:
//      a. Receives an optional JSON body with user-specific data
//      b. Calls the Bland API to authorize a session for the agent
//      c. Returns the session token and agent ID to the frontend
// ---------------------------------------------------------------------------
app.post("/authorize", async (req, res) => {
  try {
    // Build the Bland API authorization URL using the agent ID.
    const authorizeUrl = `https://api.bland.ai/v1/agents/${BLAND_AGENT_ID}/authorize`;

    // Extract any user-specific data from the frontend request.
    // The frontend can send data like { name: "John" } in the request body.
    // This data gets injected into the agent's prompt as template variables.
    const requestData = req.body.request_data || {};

    console.log("Authorizing new session...");
    console.log("Request data:", JSON.stringify(requestData));

    // Call the Bland API to create a session token.
    // Headers:
    //   - Authorization: Your raw API key (no "Bearer" prefix)
    //   - Content-Type: application/json
    const response = await axios.post(
      authorizeUrl,
      { request_data: requestData },
      {
        headers: {
          Authorization: BLAND_API_KEY,
          "Content-Type": "application/json",
        },
      }
    );

    const data = response.data;

    // Verify the response was successful.
    if (data.status === "success") {
      console.log("Session authorized successfully.");

      // Return the token and agent ID to the frontend.
      // The frontend needs both to initialize BlandWebClient.
      res.json({
        token: data.token,
        agentId: BLAND_AGENT_ID,
      });
    } else {
      // The API returned an unexpected format. Log it and send an error.
      console.error("Unexpected Bland API response:", data);
      res.status(500).json({
        error: "Failed to authorize session. Unexpected response from Bland API.",
      });
    }
  } catch (error) {
    // Handle errors from the Bland API or network issues.
    const statusCode = error.response?.status || 500;
    const errorMessage =
      error.response?.data?.message || error.message || "Unknown error";

    console.error(`Authorization failed (HTTP ${statusCode}):`, errorMessage);

    res.status(statusCode).json({
      error: `Failed to authorize session: ${errorMessage}`,
    });
  }
});

// ---------------------------------------------------------------------------
// 5. Health check endpoint (optional).
//    Useful for monitoring and load balancers to verify the server is running.
// ---------------------------------------------------------------------------
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    agentId: BLAND_AGENT_ID,
    timestamp: new Date().toISOString(),
  });
});

// ---------------------------------------------------------------------------
// 6. Start the server.
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log();
  console.log("===========================================");
  console.log("  Bland AI Web Voice Agent Server");
  console.log("===========================================");
  console.log();
  console.log(`  Server running at:  http://localhost:${PORT}`);
  console.log(`  Agent ID:           ${BLAND_AGENT_ID}`);
  console.log(`  Health check:       http://localhost:${PORT}/health`);
  console.log();
  console.log("  Open http://localhost:" + PORT + " in your browser to start.");
  console.log();
});
