// Speed to Lead: Webhook Receiver - Node.js (Express)
//
// This server exposes two endpoints:
//
//   POST /webhook/lead-form
//     Receives new lead data from your website form (or a form builder like
//     Typeform, HubSpot, etc.) and immediately triggers a Bland AI call to
//     that lead. This is the core of speed to lead: the lead fills out a
//     form and their phone rings within seconds.
//
//   POST /webhook/call-complete
//     Receives post-call data from Bland AI after each call finishes. This
//     includes the full transcript, summary, recording URL, call duration,
//     and any variables extracted during the conversation. Use this data to
//     update your CRM, score leads, and trigger follow-up actions.
//
// Usage:
//   1. Copy .env.example to .env and add your credentials.
//   2. Install dependencies: npm install express axios dotenv
//   3. Run: node webhookReceiver.js
//   4. The server starts on http://localhost:3000
//   5. For production or testing with Bland webhooks, expose with ngrok:
//      ngrok http 3000
//
// Dependencies:
//   npm install express axios dotenv

const express = require("express");
require("dotenv").config();

// Import the callLead function from leadCaller.js in the same directory.
// This handles all the Bland AI call logic so we do not duplicate it here.
const { callLead } = require("./leadCaller");

// ---------------------------------------------------------------------------
// Create the Express application and enable JSON body parsing.
// ---------------------------------------------------------------------------
const app = express();
app.use(express.json());

// ---------------------------------------------------------------------------
// In-memory storage for tracking leads and call results.
// In production, replace this with a real database (PostgreSQL, MongoDB, etc.)
// or push data directly into your CRM.
// ---------------------------------------------------------------------------
const leadsDb = [];
const callResultsDb = [];

// ===========================================================================
// Helper Functions
// ===========================================================================

/**
 * logEvent(eventType, data)
 *
 * Log a structured event with a UTC timestamp for debugging.
 * In production, replace this with a proper logging framework
 * (e.g., Winston, Pino, Datadog, etc.).
 *
 * @param {string} eventType - A label for the event (e.g., "NEW_LEAD").
 * @param {object} data - The event data to log.
 */
function logEvent(eventType, data) {
  const timestamp = new Date().toISOString();
  console.log();
  console.log("=".repeat(60));
  console.log(`[${timestamp}] ${eventType}`);
  console.log("=".repeat(60));
  console.log(JSON.stringify(data, null, 2));
  console.log();
}

/**
 * validateLeadData(data)
 *
 * Validate that the incoming lead data has all required fields.
 * This prevents calling the Bland API with incomplete data, which
 * would result in an error or a poorly personalized call.
 *
 * @param {object} data - The incoming lead form data.
 * @returns {{ valid: boolean, error: string|null }}
 */
function validateLeadData(data) {
  // Check for required fields and return a specific error for each.
  if (!data.name) {
    return { valid: false, error: "Lead name is required." };
  }
  if (!data.phone) {
    return { valid: false, error: "Lead phone number is required." };
  }
  if (!data.email) {
    return { valid: false, error: "Lead email is required." };
  }

  // Basic phone number format check. E.164 requires a leading "+".
  if (!data.phone.startsWith("+")) {
    return {
      valid: false,
      error:
        "Phone number must be in E.164 format (e.g., +15551234567). " +
        "It must start with a + followed by the country code.",
    };
  }

  return { valid: true, error: null };
}

/**
 * pushToCrm(leadData, callData)
 *
 * Push lead and call data to your CRM.
 * This is a placeholder. Replace the contents with actual API calls
 * to Salesforce, HubSpot, Pipedrive, Close, or your CRM of choice.
 *
 * @param {object} leadData - The original lead form data.
 * @param {object} callData - The post-call data from Bland AI.
 */
function pushToCrm(leadData, callData) {
  // -----------------------------------------------------------------------
  // PLACEHOLDER: Replace this section with your actual CRM integration.
  //
  // Example for HubSpot:
  //   const hubspotUrl = "https://api.hubapi.com/crm/v3/objects/contacts";
  //   await axios.post(hubspotUrl, {
  //     properties: {
  //       firstname: leadData.name.split(" ")[0],
  //       lastname: leadData.name.split(" ").slice(1).join(" "),
  //       email: leadData.email,
  //       phone: leadData.phone,
  //       lead_status: callData.is_qualified ? "QUALIFIED" : "UNQUALIFIED",
  //     },
  //   }, { headers: { Authorization: `Bearer ${HUBSPOT_API_KEY}` } });
  // -----------------------------------------------------------------------

  console.log("[CRM] Would push the following data to CRM:");
  console.log(`  Lead: ${leadData.name || "Unknown"} (${leadData.email || "Unknown"})`);
  console.log(`  Call ID: ${callData.call_id || "N/A"}`);
  console.log(`  Status: ${callData.status || "N/A"}`);
  console.log(`  Answered by: ${callData.answered_by || "N/A"}`);
  const summaryPreview = (callData.summary || "N/A").substring(0, 100);
  console.log(`  Summary: ${summaryPreview}...`);
  console.log();
}

// ===========================================================================
// Routes
// ===========================================================================

// POST /webhook/lead-form
//
// Receives a new lead form submission and immediately triggers a Bland AI
// call to qualify the lead. This is the speed-to-lead endpoint: the time
// between form submission and phone ringing should be under 10 seconds.
//
// Expected JSON body:
// {
//   "name": "Jane Smith",
//   "phone": "+15551234567",
//   "email": "jane@example.com",
//   "source": "Website Contact Form",   (optional, defaults to "Direct")
//   "interest": "Enterprise Plan"        (optional, defaults to "General Inquiry")
// }
app.post("/webhook/lead-form", async (req, res) => {
  const data = req.body;

  // If the body is empty or not JSON, return an error.
  if (!data || Object.keys(data).length === 0) {
    return res.status(400).json({ error: "Request body must be valid JSON." });
  }

  // Log the incoming lead for debugging.
  logEvent("NEW_LEAD_RECEIVED", data);

  // Validate required fields (name, phone, email).
  const { valid, error } = validateLeadData(data);
  if (!valid) {
    return res.status(400).json({ error });
  }

  // Extract lead fields with sensible defaults for optional ones.
  const name = data.name;
  const phone = data.phone;
  const email = data.email;

  // "source" tells the agent where the lead came from so it can reference
  // it in conversation (e.g., "I saw you filled out our website form").
  const source = data.source || "Direct";

  // "interest" tells the agent what the lead was looking at so the
  // conversation starts with relevant context.
  const interest = data.interest || "General Inquiry";

  // Store the lead in our in-memory database.
  // In production, save this to your real database or CRM.
  const leadRecord = {
    name,
    phone,
    email,
    source,
    interest,
    received_at: new Date().toISOString(),
    call_id: null,       // Filled after the Bland API responds
    call_status: null,   // Updated when the call completes
  };

  // Immediately trigger a Bland AI call to the lead.
  // This is the core of speed to lead. callLead() sends the API request
  // and returns almost instantly because the call is placed asynchronously
  // by Bland's infrastructure.
  console.log(`Triggering instant call to ${name} at ${phone}...`);
  const result = await callLead(name, phone, email, source, interest);

  // Handle the API response.
  if (result && result.status === "success") {
    // The call was successfully queued. Save the call_id for tracking.
    const callId = result.call_id || "unknown";
    leadRecord.call_id = callId;
    leadsDb.push(leadRecord);

    logEvent("CALL_QUEUED", {
      lead_name: name,
      phone,
      call_id: callId,
    });

    return res.status(201).json({
      status: "success",
      message: `Call queued for ${name}. Phone will ring within seconds.`,
      call_id: callId,
    });
  } else {
    // The Bland API returned an error or no response.
    const errorDetail = result || { error: "No response from Bland API" };

    logEvent("CALL_FAILED", {
      lead_name: name,
      phone,
      error: errorDetail,
    });

    return res.status(500).json({
      status: "error",
      message: "Failed to queue the call. Check server logs for details.",
      detail: errorDetail,
    });
  }
});

// POST /webhook/call-complete
//
// Receives post-call data from Bland AI after a qualification call finishes.
// Bland automatically sends this webhook when the call ends.
//
// The payload includes:
//   - call_id: Unique identifier for the call
//   - status: "completed", "failed", "no-answer", etc.
//   - answered_by: "human" or "voicemail"
//   - call_length: Duration in minutes
//   - transcripts: Array of transcript objects with speaker labels
//   - concatenated_transcript: Full transcript as a single string
//   - summary: AI-generated summary of the conversation
//   - variables: Any variables extracted during the call
//   - recording_url: URL to the call recording (if recording was enabled)
//   - price: Cost of the call in USD
app.post("/webhook/call-complete", (req, res) => {
  const data = req.body;

  // If the payload is empty, return an error.
  if (!data || Object.keys(data).length === 0) {
    return res.status(400).json({ error: "Empty webhook payload." });
  }

  // Log the full webhook payload for debugging.
  logEvent("CALL_COMPLETE_WEBHOOK", data);

  // Extract key fields from the webhook payload.
  const callId = data.call_id || "unknown";
  const status = data.status || "unknown";
  const answeredBy = data.answered_by || "unknown";
  const callLength = data.call_length || 0;
  const transcript = data.concatenated_transcript || "";
  const summary = data.summary || "";
  const variables = data.variables || {};
  const recordingUrl = data.recording_url || "";
  const price = data.price || 0;

  // Determine if the lead was qualified based on the call outcome.
  // You can customize this logic based on the variables your prompt
  // instructs the AI to extract during the conversation.
  const isQualified = variables.qualified || false;
  const wasTransferred = variables.transferred || false;
  const budget = variables.budget || "Not discussed";
  const timeline = variables.timeline || "Not discussed";

  // Build a structured result record.
  const callResult = {
    call_id: callId,
    status,
    answered_by: answeredBy,
    call_length_minutes: callLength,
    summary,
    is_qualified: isQualified,
    was_transferred: wasTransferred,
    budget,
    timeline,
    recording_url: recordingUrl,
    price_usd: price,
    processed_at: new Date().toISOString(),
  };

  // Store the result in memory.
  callResultsDb.push(callResult);

  // Log a human-readable summary of the call outcome.
  console.log();
  console.log("-".repeat(60));
  console.log("CALL RESULT SUMMARY");
  console.log("-".repeat(60));
  console.log(`  Call ID:       ${callId}`);
  console.log(`  Status:        ${status}`);
  console.log(`  Answered by:   ${answeredBy}`);
  console.log(`  Duration:      ${callLength} minutes`);
  console.log(`  Qualified:     ${isQualified ? "Yes" : "No"}`);
  console.log(`  Transferred:   ${wasTransferred ? "Yes" : "No"}`);
  console.log(`  Budget:        ${budget}`);
  console.log(`  Timeline:      ${timeline}`);
  console.log(`  Cost:          $${Number(price).toFixed(4)}`);
  console.log(`  Recording:     ${recordingUrl || "N/A"}`);
  console.log();
  const summaryTruncated = summary.length > 200 ? summary.substring(0, 200) + "..." : summary;
  console.log(`  Summary: ${summaryTruncated}`);
  console.log("-".repeat(60));
  console.log();

  // Find the matching lead record and update it with call results.
  // This connects the original lead data with the call outcome.
  let matchingLead = null;
  for (const lead of leadsDb) {
    if (lead.call_id === callId) {
      lead.call_status = status;
      lead.answered_by = answeredBy;
      lead.is_qualified = isQualified;
      matchingLead = lead;
      break;
    }
  }

  // Push results to your CRM. The pushToCrm function is a placeholder.
  // Replace it with actual API calls to Salesforce, HubSpot, Pipedrive, etc.
  if (matchingLead) {
    pushToCrm(matchingLead, callResult);
  } else {
    // If we do not have a matching lead (e.g., the server restarted),
    // still log the CRM push with whatever data is available.
    pushToCrm({ name: "Unknown", email: "Unknown" }, callResult);
  }

  // Handle different call outcomes with specific follow-up actions.
  if (answeredBy === "voicemail") {
    // The lead did not answer. Consider scheduling a retry.
    console.log("[ACTION] Lead went to voicemail. Consider scheduling a retry call.");
    console.log("         You could use the Bland batch API to retry in 30 minutes.");
  } else if (isQualified && !wasTransferred) {
    // Qualified but not transferred (sales rep may have been unavailable).
    console.log("[ACTION] Qualified lead was not transferred.");
    console.log("         Notify sales team immediately for a manual follow-up.");
  } else if (isQualified && wasTransferred) {
    // Best case: qualified and transferred to a sales rep.
    console.log("[ACTION] Qualified lead was transferred to sales. Update CRM status.");
  } else {
    // Not qualified. Add to nurture sequence.
    console.log("[ACTION] Lead was not qualified. Add to email nurture sequence.");
  }

  // Return a 200 OK to acknowledge receipt of the webhook.
  // Bland expects a 200 response. If you return an error, Bland may
  // retry the webhook delivery.
  return res.status(200).json({
    status: "received",
    call_id: callId,
    processed: true,
  });
});

// GET /health
// Simple health check endpoint for monitoring. Returns the number of
// leads received and calls completed since the server started.
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    leads_received: leadsDb.length,
    calls_completed: callResultsDb.length,
  });
});

// ===========================================================================
// Start the Express server.
// ===========================================================================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log();
  console.log("=".repeat(60));
  console.log("Speed to Lead Webhook Server (Node.js / Express)");
  console.log("=".repeat(60));
  console.log();
  console.log("Endpoints:");
  console.log("  POST /webhook/lead-form      Receive lead form submissions");
  console.log("  POST /webhook/call-complete   Receive post-call results from Bland");
  console.log("  GET  /health                  Health check");
  console.log();
  console.log("For local testing with Bland webhooks, expose with ngrok:");
  console.log(`  ngrok http ${PORT}`);
  console.log();
  console.log("Then update WEBHOOK_URL in .env with your ngrok HTTPS URL:");
  console.log("  https://your-id.ngrok.io/webhook/call-complete");
  console.log();
  console.log("=".repeat(60));
  console.log();
});
