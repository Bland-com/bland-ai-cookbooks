/**
 * Bland AI - Send a Call with Citation Schemas and Auto-Schedule Follow-Ups (Node.js)
 *
 * This script demonstrates the full citation workflow:
 *   1. Send a call with an analysis schema so Bland extracts structured data
 *      from the conversation automatically.
 *   2. Wait for the call to complete and poll for results.
 *   3. Read the citation data that comes back, which includes the extracted
 *      fields and links each value to the exact utterance where it was mentioned.
 *   4. Based on the extracted data, automatically schedule a follow-up call
 *      and send an SMS confirmation.
 *
 * Citation schemas let you define fields (like customer_name, email,
 * follow_up_date) that the AI extracts from the transcript after the call.
 * Each extracted value is paired with a "citation" pointing to the specific
 * part of the conversation where the information came from. This makes
 * your post-call data auditable and trustworthy.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key and phone number.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node callWithCitations.js
 *
 * The script will:
 *    - Send a call with an analysis schema attached
 *    - Poll until the call completes
 *    - Display the extracted citation data
 *    - Demonstrate how to auto-schedule a follow-up based on the results
 */

require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

// The phone number to call, in E.164 format (e.g., +15551234567).
const PHONE_NUMBER = process.env.PHONE_NUMBER;

// Optional: Your SMS-configured Bland phone number for sending follow-up texts.
// If not set, the SMS follow-up step is skipped.
const FROM_NUMBER = process.env.FROM_NUMBER;

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

if (!PHONE_NUMBER) {
  console.error("Error: PHONE_NUMBER is not set.");
  console.error("Add the phone number to call in E.164 format to .env.");
  process.exit(1);
}

// ---------------------------------------------------------------------------
// HTTP headers (reused for all requests)
// ---------------------------------------------------------------------------

// Bland uses a simple API key in the Authorization header
// (no "Bearer" prefix needed).
const headers = {
  Authorization: API_KEY,
  "Content-Type": "application/json",
};

// ---------------------------------------------------------------------------
// Helper: sleep for N milliseconds
// ---------------------------------------------------------------------------

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

async function callWithCitations() {
  // =========================================================================
  // Step 1: Understand citation schemas
  // =========================================================================

  // Citation schemas define the structured fields you want extracted from every
  // call. You create them once in the Bland dashboard (or via the API), then
  // reference them by ID when sending calls.
  //
  // Each schema has an array of fields. Each field specifies:
  //   - name: The field name (e.g., "customer_email")
  //   - type: "string", "integer", "boolean", or "enum"
  //   - description: Instructions for the AI on what to extract
  //
  // After the call, Bland returns:
  //   - analysis: An object with each field name as a key and the extracted
  //     value as the value.
  //   - citations: An array linking each extracted value to the specific
  //     transcript utterance where the information was mentioned.
  //
  // For this example, we use the analysis_schema parameter directly on the
  // call (which works the same way as citation_schema_ids, but is defined
  // inline rather than referencing a pre-created schema).

  console.log("=".repeat(60));
  console.log("CALL WITH CITATIONS AND AUTO FOLLOW-UP");
  console.log("=".repeat(60));
  console.log();

  // =========================================================================
  // Step 2: Send the call with an analysis schema
  // =========================================================================

  const AGENT_PROMPT = `You are Alex, a friendly follow-up specialist at CloudSync Software.
You are calling a customer who recently signed up for a free trial.

Your goals:
1. Introduce yourself and thank them for trying CloudSync.
2. Ask how their experience has been so far.
3. Find out if they have any questions about the product.
4. Ask if they would like to schedule a follow-up call or demo with a product specialist.
5. If they want a follow-up, ask for their preferred date and time.
6. Collect their email address for sending a calendar invite.
7. Thank them and wrap up.

Keep the conversation natural and friendly. Do not rush. Listen to their
feedback and respond thoughtfully. If they are not interested in a follow-up,
thank them and let them know they can reach out anytime.

Important: Make sure to ask for their email and preferred follow-up time
so we can schedule the next touchpoint.`;

  // The analysis schema defines what to extract from the conversation.
  // Each field maps to a specific piece of information the agent should collect.
  const analysisSchema = {
    // String field: the customer's full name.
    customer_name: "The customer's full name as mentioned during the call.",

    // String field: their email address for follow-up communication.
    customer_email: "The customer's email address.",

    // String field: when they want the follow-up call.
    preferred_follow_up_time:
      "The customer's preferred date and time for a follow-up call. " +
      "Format as a human-readable string like 'Tuesday at 2 PM' or " +
      "'March 20th at 10 AM'. Return null if they declined a follow-up.",

    // Boolean field: did they agree to a follow-up?
    wants_follow_up:
      "Whether the customer agreed to schedule a follow-up call or demo. " +
      "true if yes, false if no.",

    // String field: overall sentiment.
    customer_sentiment:
      "The customer's overall sentiment about the product. " +
      "One of: positive, neutral, or negative.",

    // String field: a concise summary of their feedback.
    feedback_summary:
      "A one to two sentence summary of the customer's feedback " +
      "about their experience with CloudSync.",
  };

  const callPayload = {
    // The phone number to call.
    phone_number: PHONE_NUMBER,

    // The agent prompt that drives the conversation.
    task: AGENT_PROMPT,

    // The analysis schema. If you have pre-created citation schemas in the
    // Bland dashboard, use citation_schema_ids instead:
    //
    //   citation_schema_ids: ["schema-uuid-1", "schema-uuid-2"]
    //
    // Both produce structured data with citations.
    analysis_schema: analysisSchema,

    // Record the call so we can verify the transcript later.
    record: true,

    // Limit the call to 5 minutes for this demo.
    max_duration: 5,

    // Request the citations webhook event.
    webhook_events: ["citations"],

    // A custom summary prompt focused on follow-up actions.
    summary_prompt:
      "Summarize this call in three bullet points: " +
      "(1) the customer's overall feedback, " +
      "(2) whether they want a follow-up and when, " +
      "(3) any action items for the team.",
  };

  console.log("Sending call to " + PHONE_NUMBER + "...");
  console.log();

  let callId;

  try {
    const response = await axios.post(BASE_URL + "/calls", callPayload, {
      headers,
      timeout: 30000,
    });

    callId = response.data.call_id;

    if (!callId) {
      console.error("Error: No call_id in response.");
      console.error("Response: " + JSON.stringify(response.data, null, 2));
      process.exit(1);
    }

    console.log("Call queued successfully!");
    console.log("  Call ID: " + callId);
    console.log();
  } catch (error) {
    console.error("Error sending call: " + (error.message || error));
    if (error.response) {
      console.error("Response: " + JSON.stringify(error.response.data, null, 2));
    }
    process.exit(1);
  }

  // =========================================================================
  // Step 3: Poll for call completion
  // =========================================================================

  console.log("Waiting for the call to complete...");
  console.log("(Answer your phone when it rings!)");
  console.log();

  const MAX_POLL_ATTEMPTS = 60; // Poll for up to 5 minutes
  const POLL_INTERVAL = 5000;   // 5 seconds between polls

  let callCompleted = false;

  for (let attempt = 0; attempt < MAX_POLL_ATTEMPTS; attempt++) {
    try {
      const pollResponse = await axios.get(
        BASE_URL + "/calls/" + callId,
        { headers, timeout: 15000 }
      );
      const pollData = pollResponse.data;

      const status = pollData.status || "unknown";
      const completed = pollData.completed || false;

      if (completed || status === "completed") {
        console.log("Call completed!");
        console.log();
        callCompleted = true;
        break;
      }

      const elapsed = (attempt + 1) * 5;
      console.log(
        "  Still in progress... (" + elapsed + "s elapsed, status: " + status + ")"
      );
    } catch (_) {
      // Ignore transient errors during polling.
    }

    await sleep(POLL_INTERVAL);
  }

  if (!callCompleted) {
    console.log("Timed out waiting for the call to complete.");
    console.log("You can still check the results later using:");
    console.log("  node analyzeCall.js " + callId);
    process.exit(0);
  }

  // =========================================================================
  // Step 4: Display call results and citations
  // =========================================================================

  let callResult;

  try {
    const finalResponse = await axios.get(
      BASE_URL + "/calls/" + callId,
      { headers, timeout: 15000 }
    );
    callResult = finalResponse.data;
  } catch (error) {
    console.error("Error fetching final call data: " + error.message);
    process.exit(1);
  }

  // Display basic call info.
  console.log("=".repeat(60));
  console.log("CALL RESULTS");
  console.log("=".repeat(60));
  console.log();
  console.log("  Call ID:       " + (callResult.call_id || "N/A"));
  console.log("  Duration:      " + (callResult.call_length || "N/A") + " min");
  console.log("  Ended By:      " + (callResult.call_ended_by || "N/A"));
  console.log("  Cost:          $" + (callResult.price || "N/A"));
  console.log();

  // Display the AI-generated summary.
  const summary = callResult.summary || "";
  if (summary) {
    console.log("Summary:");
    for (const line of summary.split("\n")) {
      console.log("  " + line);
    }
    console.log();
  }

  // Display the analysis results (extracted fields).
  const analysis = callResult.analysis || {};
  const analysisKeys = Object.keys(analysis);

  if (analysisKeys.length > 0) {
    console.log("=".repeat(60));
    console.log("EXTRACTED DATA (from analysis schema)");
    console.log("=".repeat(60));
    console.log();
    for (const [fieldName, fieldValue] of Object.entries(analysis)) {
      console.log("  " + fieldName + ": " + fieldValue);
    }
    console.log();
  } else {
    console.log("No analysis data available yet.");
    console.log("Analysis data may take a few seconds to populate after the call.");
    console.log("Try running: node analyzeCall.js " + callId);
    console.log();
  }

  // Display citations if available.
  // Citations link each extracted value to the specific utterance in the
  // transcript where the information was mentioned.
  //
  // Citation format:
  // {
  //   "field": "customer_email",
  //   "value": "alex@example.com",
  //   "utterance": "Sure, my email is alex@example.com.",
  //   "speaker": "user",
  //   "confidence": 0.95
  // }
  const citations = callResult.citations || [];

  if (citations.length > 0) {
    console.log("=".repeat(60));
    console.log("CITATIONS (linking data to transcript)");
    console.log("=".repeat(60));
    console.log();
    console.log("Each citation shows where a piece of extracted data came from");
    console.log("in the conversation, so you can verify and audit the results.");
    console.log();

    for (let i = 0; i < citations.length; i++) {
      const citation = citations[i];
      console.log("  Citation " + (i + 1) + ":");

      // The field name this citation relates to.
      const field = citation.field || citation.key || "unknown";
      console.log("    Field:      " + field);

      // The extracted value for this field.
      const value = citation.value || "N/A";
      console.log("    Value:      " + value);

      // The exact utterance where this information was mentioned.
      const utterance = citation.utterance || citation.text || "N/A";
      console.log('    Utterance:  "' + utterance + '"');

      // Who said it: "user" or "agent".
      const speaker = citation.speaker || "N/A";
      console.log("    Speaker:    " + speaker);

      // Confidence score (0 to 1).
      const confidence = citation.confidence;
      if (confidence != null) {
        console.log("    Confidence: " + Math.round(confidence * 100) + "%");
      }

      console.log();
    }
  } else {
    console.log("No citations available yet.");
    console.log("Citations arrive in the delayed webhook (30 to 60 seconds after");
    console.log("the call). You can also check the call details in the dashboard.");
    console.log();
  }

  // =========================================================================
  // Step 5: Auto-schedule a follow-up based on extracted data
  // =========================================================================

  console.log("=".repeat(60));
  console.log("AUTO FOLLOW-UP SCHEDULING");
  console.log("=".repeat(60));
  console.log();

  const wantsFollowUp = analysis.wants_follow_up;
  const followUpTime = analysis.preferred_follow_up_time;
  const customerName = analysis.customer_name || "the customer";
  const customerEmail = analysis.customer_email;

  if (wantsFollowUp && followUpTime) {
    console.log("The customer wants a follow-up!");
    console.log("  Name:           " + customerName);
    console.log("  Email:          " + (customerEmail || "N/A"));
    console.log("  Preferred Time: " + followUpTime);
    console.log();

    // Schedule a follow-up call.
    // In production, you would parse the followUpTime into a proper datetime
    // and pass it as start_time.
    const followUpPayload = {
      phone_number: PHONE_NUMBER,
      task:
        "You are Alex from CloudSync Software, calling back " +
        customerName +
        " for a scheduled product demo. They signed up for a free trial " +
        "and expressed interest in learning more. Walk them through " +
        "the key features and answer any questions they have. " +
        "Their feedback from the last call: " +
        (analysis.feedback_summary || "No prior feedback recorded."),
      max_duration: 15,
      record: true,
      // In production, parse the preferred time and set start_time:
      // start_time: "2026-03-20 14:00:00 -05:00",
      request_data: {
        customer_name: customerName,
        customer_email: customerEmail || "",
        original_call_id: callId,
      },
      analysis_schema: {
        demo_completed:
          "Was the product demo completed successfully? true or false.",
        interested_in_purchase:
          "Is the customer interested in purchasing? true or false.",
        plan_discussed:
          "Which plan was discussed? starter, professional, enterprise, or none.",
        next_steps: "What are the agreed next steps after this call?",
      },
    };

    console.log("Follow-up call payload (ready to send):");
    console.log(JSON.stringify(followUpPayload, null, 2));
    console.log();

    // Uncomment to actually send the follow-up call:
    // const followUpResponse = await axios.post(
    //   BASE_URL + "/calls",
    //   followUpPayload,
    //   { headers, timeout: 30000 }
    // );
    // console.log("Follow-up call scheduled! Call ID: " +
    //   followUpResponse.data.call_id);

    // Send an SMS confirmation if FROM_NUMBER is configured.
    if (FROM_NUMBER) {
      const smsMessage =
        "Hi " + customerName + "! This is Alex from CloudSync. " +
        "Thanks for chatting today. As discussed, we have your follow-up " +
        "demo scheduled for " + followUpTime + ". Looking forward to it! " +
        "Reply to this text if you need to reschedule.";

      const smsPayload = {
        phone_number: PHONE_NUMBER,
        from: FROM_NUMBER,
        message: smsMessage,
      };

      console.log("SMS confirmation payload (ready to send):");
      console.log(JSON.stringify(smsPayload, null, 2));
      console.log();

      // Uncomment to actually send the SMS:
      // await axios.post(BASE_URL + "/sms/send", smsPayload, {
      //   headers,
      //   timeout: 30000,
      // });
      // console.log("SMS confirmation sent!");
    } else {
      console.log("Skipping SMS confirmation (FROM_NUMBER not set in .env).");
      console.log(
        "Set FROM_NUMBER to an SMS-configured Bland number to enable this."
      );
      console.log();
    }
  } else if (wantsFollowUp === false) {
    console.log("The customer declined a follow-up call.");
    console.log("No follow-up scheduled. Their feedback has been recorded:");
    console.log(
      "  Sentiment: " + (analysis.customer_sentiment || "N/A")
    );
    console.log(
      "  Feedback:  " + (analysis.feedback_summary || "N/A")
    );
    console.log();
  } else {
    console.log("Could not determine follow-up preference from the call data.");
    console.log("This may happen if the call was very short or the analysis is");
    console.log("still processing. Check the dashboard for full results.");
    console.log();
  }

  // =========================================================================
  // Done
  // =========================================================================

  console.log("=".repeat(60));
  console.log("WHAT YOU LEARNED");
  console.log("=".repeat(60));
  console.log();
  console.log("  1. How to attach an analysis_schema (or citation_schema_ids)");
  console.log("     to a call so Bland extracts structured data automatically.");
  console.log();
  console.log("  2. How citations link each extracted value back to the exact");
  console.log("     utterance in the transcript, making the data auditable.");
  console.log();
  console.log("  3. How to use the extracted data to auto-schedule follow-up");
  console.log("     calls and send SMS confirmations without manual work.");
  console.log();
  console.log("  In production, replace polling with webhooks for real-time");
  console.log("  processing. See the webhook_listener scripts in this cookbook.");
  console.log();
  console.log("Done.");
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

callWithCitations();
