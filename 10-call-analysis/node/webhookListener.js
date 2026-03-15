/**
 * Bland AI - Webhook Listener (Node.js)
 *
 * This script runs an Express server that listens for post-call webhook
 * payloads from Bland AI. When a call completes, Bland sends a POST request
 * to your webhook URL with the full call data. This script receives that
 * data, logs key information, and demonstrates how you would process and
 * store it.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key (optional for webhooks).
 *    2. Install dependencies: npm install express dotenv
 *    3. Run: node webhookListener.js
 *    4. The server starts on port 3000 (or the PORT in your .env).
 *    5. Expose the server to the internet using ngrok or a similar tool:
 *           ngrok http 3000
 *    6. Copy the ngrok HTTPS URL and use it as the webhook parameter when
 *       creating calls:
 *           "webhook": "https://abc123.ngrok.io/webhook/call-complete"
 *
 * The server handles two types of webhook payloads:
 *    - Immediate payload: Arrives right when the call ends. Contains the
 *      transcript, summary, variables, disposition, and basic metadata.
 *    - Delayed payload: Arrives 30 to 60 seconds later. Contains the
 *      corrected transcript with confidence scores and citation data.
 */

// Load environment variables from .env file.
require("dotenv").config();
const express = require("express");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Port for the Express server. Defaults to 3000 if not set.
const PORT = parseInt(process.env.PORT || "3000", 10);

// ---------------------------------------------------------------------------
// Express app setup
// ---------------------------------------------------------------------------

// Create the Express application instance.
const app = express();

// Parse incoming JSON request bodies. Bland sends all webhook payloads
// as JSON, so this middleware is required for every webhook endpoint.
app.use(express.json());

// ---------------------------------------------------------------------------
// In-memory storage (placeholder for a real database)
// ---------------------------------------------------------------------------

// In production, you would store webhook payloads in a database (PostgreSQL,
// MongoDB, etc.). This object simulates that by storing payloads in memory,
// keyed by call_id. It resets when the server restarts.
const callStore = {};

/**
 * Save call data to the in-memory store.
 *
 * In production, replace this with your actual database logic. For example:
 *   - Insert a row into a PostgreSQL table
 *   - Save a document in MongoDB
 *   - Push to a message queue for async processing
 *
 * @param {string} callId - The unique identifier for the call.
 * @param {object} data - The full webhook payload object.
 */
function saveCallData(callId, data) {
  callStore[callId] = data;
  console.log(
    `  [DB] Saved call ${callId} to store. Total calls stored: ${Object.keys(callStore).length}`
  );
}

/**
 * Merge additional data into an existing call record.
 *
 * This is used when the delayed webhook arrives with corrected transcript
 * and citation data. The delayed payload should be merged with the
 * immediate payload using the call_id as the key.
 *
 * @param {string} callId - The unique identifier for the call.
 * @param {object} updates - An object of fields to merge into the existing record.
 */
function updateCallData(callId, updates) {
  if (callStore[callId]) {
    // Merge the new fields into the existing record.
    Object.assign(callStore[callId], updates);
    console.log(`  [DB] Updated call ${callId} with additional data.`);
  } else {
    // If the immediate payload has not arrived yet (unlikely but possible),
    // store the delayed data as its own record.
    callStore[callId] = updates;
    console.log(
      `  [DB] Stored delayed data for call ${callId} (no immediate data found).`
    );
  }
}

// ---------------------------------------------------------------------------
// Webhook endpoint: POST /webhook/call-complete
// ---------------------------------------------------------------------------

app.post("/webhook/call-complete", (req, res) => {
  /**
   * Receives the post-call webhook from Bland AI.
   *
   * Bland sends two POST requests per call:
   *   1. Immediate payload (right when the call ends):
   *      Contains call_id, call_length, summary, transcripts, variables,
   *      disposition_tag, and other core fields.
   *   2. Delayed payload (30 to 60 seconds later):
   *      Contains corrected_transcript (with speaker labels and confidence
   *      scores) and citations (linking variables to utterances).
   *
   * This handler processes both types. It distinguishes them by checking
   * whether the payload contains the "corrected_transcript" field.
   */

  // Get the JSON payload from the request body.
  const payload = req.body;

  // If the body is empty or not valid JSON, return a 400 error.
  if (!payload || typeof payload !== "object") {
    console.log("[WARN] Received webhook with no JSON body.");
    return res.status(400).json({ error: "No JSON body provided" });
  }

  // Extract the call_id, which is present in both immediate and delayed payloads.
  const callId = payload.call_id || "unknown";

  // Print a timestamp for logging.
  const timestamp = new Date().toISOString().replace("T", " ").substring(0, 19);

  // -------------------------------------------------------------------------
  // Check if this is the delayed payload (contains corrected_transcript)
  // -------------------------------------------------------------------------

  if (payload.corrected_transcript !== undefined) {
    // This is the delayed payload with corrected transcript and citations.
    console.log();
    console.log("=".repeat(60));
    console.log(`[${timestamp}] DELAYED WEBHOOK RECEIVED`);
    console.log("=".repeat(60));
    console.log(`  Call ID: ${callId}`);

    // The corrected transcript includes speaker labels and confidence scores.
    const corrected = payload.corrected_transcript || {};
    if (corrected && typeof corrected === "object") {
      console.log();
      console.log("  Corrected Transcript:");

      // The corrected transcript may contain a "segments" array with
      // detailed utterance data including confidence and timestamps.
      const segments = corrected.segments || [];
      if (segments.length > 0) {
        // Show the first 5 segments as a preview.
        const preview = segments.slice(0, 5);
        for (const segment of preview) {
          const speaker = segment.speaker || "unknown";
          const text = segment.text || "";
          const confidence = segment.confidence || 0;
          // Format confidence as a percentage (e.g., 0.95 becomes "95%").
          const pct = `${Math.round(confidence * 100)}%`;
          console.log(`    [${speaker} (confidence: ${pct})] ${text}`);
        }
        if (segments.length > 5) {
          console.log(`    ... and ${segments.length - 5} more segments.`);
        }
      } else {
        // Sometimes the corrected transcript is a simple string or flat object.
        const preview = JSON.stringify(corrected, null, 4).substring(0, 500);
        console.log(`    ${preview}`);
      }
    }

    // Citations link extracted variables to specific utterances in the
    // transcript, showing exactly where each piece of information came from.
    const citations = payload.citations || [];
    if (citations.length > 0) {
      console.log();
      console.log("  Citations:");
      const citationPreview = citations.slice(0, 5);
      for (const citation of citationPreview) {
        console.log(`    ${JSON.stringify(citation)}`);
      }
      if (citations.length > 5) {
        console.log(`    ... and ${citations.length - 5} more citations.`);
      }
    }

    // Merge the delayed data into the existing call record.
    updateCallData(callId, {
      corrected_transcript: corrected,
      citations: citations,
    });
  } else {
    // -----------------------------------------------------------------------
    // This is the immediate payload with core call data
    // -----------------------------------------------------------------------

    console.log();
    console.log("=".repeat(60));
    console.log(`[${timestamp}] IMMEDIATE WEBHOOK RECEIVED`);
    console.log("=".repeat(60));

    // --- Basic call metadata ---
    console.log();
    console.log(`  Call ID:       ${callId}`);
    console.log(`  Completed:     ${payload.completed != null ? payload.completed : "N/A"}`);
    console.log(`  Inbound:       ${payload.inbound != null ? payload.inbound : "N/A"}`);
    console.log(`  Call Length:    ${payload.call_length != null ? payload.call_length : "N/A"} min`);
    console.log(`  Price:         $${payload.price != null ? payload.price : "N/A"}`);
    console.log(`  Ended By:      ${payload.call_ended_by || "N/A"}`);
    console.log(`  Error:         ${payload.error_message || "None"}`);

    // --- Disposition ---
    // The disposition_tag is the outcome label that the agent selected
    // from the dispositions list you configured on the call.
    // Example values: "Interested", "Not Interested", "Callback Requested"
    const disposition = payload.disposition_tag;
    if (disposition) {
      console.log();
      console.log(`  Disposition:   ${disposition}`);
    }

    // --- Transfer info ---
    // If the call was transferred to another number, these fields are populated.
    const transferredTo = payload.transferred_to;
    if (transferredTo) {
      console.log();
      console.log(`  Transferred To:         ${transferredTo}`);
      console.log(
        `  Pre-Transfer Duration:  ${payload.pre_transfer_duration != null ? payload.pre_transfer_duration : "N/A"} min`
      );
      console.log(
        `  Post-Transfer Duration: ${payload.post_transfer_duration != null ? payload.post_transfer_duration : "N/A"} min`
      );
    }

    // --- Summary ---
    // The AI-generated summary of the call. This follows the format
    // specified by the summary_prompt parameter (if set), or uses
    // the default Bland summary format.
    const summary = payload.summary || "";
    if (summary) {
      console.log();
      console.log("  Summary:");
      // Indent each line of the summary for readability.
      for (const line of summary.split("\n")) {
        console.log(`    ${line}`);
      }
    }

    // --- Transcript ---
    // The concatenated transcript is the full conversation as a single
    // string with speaker labels (e.g., "Agent: ... User: ...").
    const concatenated = payload.concatenated_transcript || "";
    if (concatenated) {
      console.log();
      console.log("  Transcript:");
      // Show a preview of the transcript (first 800 characters).
      const preview = concatenated.substring(0, 800);
      for (const line of preview.split("\n")) {
        console.log(`    ${line}`);
      }
      if (concatenated.length > 800) {
        console.log(
          `    ... (truncated, ${concatenated.length} total characters)`
        );
      }
    }

    // --- Variables ---
    // Variables are key-value pairs extracted or set during the call.
    // These come from the agent's prompt (e.g., collecting a name or email)
    // or from custom tool calls during the call.
    const variables = payload.variables || {};
    if (Object.keys(variables).length > 0) {
      console.log();
      console.log("  Variables:");
      for (const [key, value] of Object.entries(variables)) {
        console.log(`    ${key}: ${value}`);
      }
    }

    // --- Metadata ---
    // Custom metadata that was attached to the call when it was created.
    const metadata = payload.metadata || {};
    if (Object.keys(metadata).length > 0) {
      console.log();
      console.log("  Metadata:");
      for (const [key, value] of Object.entries(metadata)) {
        console.log(`    ${key}: ${value}`);
      }
    }

    // --- Pathway Logs ---
    // If the call used a pathway, pathway_logs contain the execution trace
    // showing which nodes were visited and what happened at each step.
    const pathwayLogs = payload.pathway_logs || [];
    if (pathwayLogs.length > 0) {
      console.log();
      console.log(`  Pathway Logs: ${pathwayLogs.length} entries`);
      // Show the first 3 log entries as a preview.
      const logPreview = pathwayLogs.slice(0, 3);
      for (let i = 0; i < logPreview.length; i++) {
        const entry = JSON.stringify(logPreview[i]).substring(0, 200);
        console.log(`    [${i}] ${entry}`);
      }
      if (pathwayLogs.length > 3) {
        console.log(`    ... and ${pathwayLogs.length - 3} more entries.`);
      }
    }

    // Save the complete payload to the in-memory store.
    saveCallData(callId, payload);
  }

  console.log();
  console.log("=".repeat(60));
  console.log();

  // Return a 200 OK response so Bland knows the webhook was received.
  // If you return a non-2xx status, Bland may retry the webhook.
  return res.json({ status: "received", call_id: callId });
});

// ---------------------------------------------------------------------------
// Health check endpoint: GET /
// ---------------------------------------------------------------------------

app.get("/", (req, res) => {
  /**
   * Simple health check endpoint. Useful for verifying the server is running
   * and for load balancer health checks in production.
   */
  return res.json({
    status: "ok",
    message: "Bland AI Webhook Listener is running.",
    calls_received: Object.keys(callStore).length,
  });
});

// ---------------------------------------------------------------------------
// List received calls: GET /calls
// ---------------------------------------------------------------------------

app.get("/calls", (req, res) => {
  /**
   * Returns a list of all call_ids that have been received via webhooks.
   * Useful for debugging and verifying that webhooks are arriving.
   */
  const callSummaries = [];

  for (const [cid, data] of Object.entries(callStore)) {
    callSummaries.push({
      call_id: cid,
      completed: data.completed,
      call_length: data.call_length,
      // Truncate the summary to 100 characters for the list view.
      summary: (data.summary || "").substring(0, 100),
      has_corrected_transcript: data.corrected_transcript !== undefined,
    });
  }

  return res.json({
    total: callSummaries.length,
    calls: callSummaries,
  });
});

// ---------------------------------------------------------------------------
// Start the server
// ---------------------------------------------------------------------------

app.listen(PORT, "0.0.0.0", () => {
  console.log("=".repeat(60));
  console.log("Bland AI Webhook Listener");
  console.log("=".repeat(60));
  console.log();
  console.log(`Listening on port ${PORT}`);
  console.log();
  console.log("Endpoints:");
  console.log("  GET  /                        Health check");
  console.log("  GET  /calls                   List received calls");
  console.log("  POST /webhook/call-complete   Receive post-call webhooks");
  console.log();
  console.log("To receive webhooks from Bland AI:");
  console.log(`  1. Expose this server to the internet (e.g., ngrok http ${PORT})`);
  console.log("  2. Set the webhook URL when creating a call:");
  console.log('     "webhook": "https://your-url/webhook/call-complete"');
  console.log();
  console.log("Press Ctrl+C to stop the server.");
  console.log();
});
