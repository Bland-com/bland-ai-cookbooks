// Custom Tool Webhook Server - Node.js (Express)
// ================================================
//
// This server receives requests from Bland AI when your agent triggers a
// custom tool during a live phone call. It simulates two common integrations:
//
//   POST /api/book      - Appointment booking system
//   POST /api/lookup    - CRM customer lookup
//
// In a real application, these endpoints would connect to your actual booking
// system (Calendly, Acuity, a custom database) and CRM (Salesforce, HubSpot,
// etc.). Here, they use simulated data to demonstrate the full cycle.
//
// The flow from Bland to your server and back:
//   1. The agent extracts data from the conversation (date, time, email, etc.)
//      using the input_schema defined in your tool.
//   2. Bland sends an HTTP POST to the URL configured in your tool schema,
//      with the extracted values injected into the request body.
//   3. This server processes the request and returns a JSON response.
//   4. Bland maps fields from the response to named variables using the
//      JSONPath expressions in the tool's "response" configuration.
//   5. The agent uses those variables to continue the conversation naturally.
//
// Usage:
//   1. Install dependencies: npm install express cors dotenv
//   2. Run: node webhookServer.js
//   3. In a separate terminal, expose the server publicly:
//        ngrok http 3001
//   4. Copy the ngrok HTTPS URL into your .env file as WEBHOOK_URL.
//   5. Then run sendCallWithTool.js in another terminal to start a call.
//
// Security note:
//   In production, always validate incoming requests. You could check a
//   shared secret header, validate the source IP, or use HMAC signatures.
//   This example is kept simple for clarity.

const express = require("express");
const cors = require("cors");
const app = express();

// Parse JSON request bodies. Bland sends tool requests as JSON.
app.use(express.json());

// Enable CORS so Bland's servers can reach these endpoints from any origin.
// In production, restrict this to specific origins if needed.
app.use(cors());

// In-memory storage for booked appointments. In a real application, this
// would be your database (PostgreSQL, MongoDB, etc.).
const appointments = [];

// ---------------------------------------------------------------------------
// Mock customer database
//
// Keyed by phone number for easy lookup during the call. In production,
// you would query your CRM or database instead.
// ---------------------------------------------------------------------------
const mockCustomers = {
  "+15551234567": {
    name: "John Smith",
    email: "john.smith@email.com",
    plan: "Premium",
    account_status: "Active",
    last_visit: "February 15, 2026",
  },
  "+15559876543": {
    name: "Sarah Johnson",
    email: "sarah.j@email.com",
    plan: "Basic",
    account_status: "Active",
    last_visit: "January 8, 2026",
  },
};

// ---------------------------------------------------------------------------
// Endpoint 1: Book an Appointment
// POST /api/book
//
// Bland's agent calls this when a caller wants to schedule an appointment.
// The agent uses the input_schema to extract these fields from conversation:
//   - date: The requested date (e.g., "2026-03-20")
//   - time: The requested time (e.g., "10:00 AM")
//   - service: What type of appointment (e.g., "Dental Checkup")
//   - customer_name: The caller's name (e.g., "John Smith")
//   - customer_phone: The caller's phone number
//
// The response must include fields that match the JSONPath expressions
// defined in the tool's "response" mapping:
//   "confirmation_number": "$.confirmation_number"  -> top-level field
//   "appointment_time":    "$.appointment_time"      -> top-level field
//   "provider_name":       "$.provider_name"         -> top-level field
//
// After this endpoint returns, the agent can reference {{confirmation_number}},
// {{appointment_time}}, and {{provider_name}} in the conversation.
// ---------------------------------------------------------------------------
app.post("/api/book", (req, res) => {
  // Extract the fields that the agent populated via {{input.property}}
  // template variables in the tool's body configuration.
  const { date, time, service, customer_name, customer_phone } = req.body;

  // Log the incoming request so you can verify the data extraction
  // is working correctly during development. This is the most useful
  // debugging step: if these values are wrong, check your input_schema.
  console.log("\n--- New Booking Request ---");
  console.log("Customer:", customer_name);
  console.log("Phone:", customer_phone);
  console.log("Service:", service);
  console.log("Date:", date);
  console.log("Time:", time);

  // Generate a random 6-digit confirmation number with a "BK-" prefix.
  // In production, this would come from your booking system.
  const confirmationNumber =
    "BK-" + Math.floor(100000 + Math.random() * 900000);

  // Build the appointment record. This stores all the details for
  // reference and also structures the response for Bland.
  const appointment = {
    confirmation_number: confirmationNumber,
    customer_name: customer_name || "Guest",
    customer_phone: customer_phone || "N/A",
    service: service || "General Checkup",
    date: date || "TBD",
    time: time || "TBD",
    // Combine date and time into a readable string the agent can speak.
    appointment_time: `${date} at ${time}`,
    // Assign a provider. In production, you would check availability
    // and assign based on scheduling rules.
    provider_name: "Dr. Sarah Chen",
    created_at: new Date().toISOString(),
  };

  // Store the appointment in memory (simulating a database write).
  appointments.push(appointment);

  console.log("Confirmation:", confirmationNumber);
  console.log("----------------------------\n");

  // Return the response to Bland. The field names at the top level
  // must match the JSONPath expressions in the tool's "response" mapping.
  //
  // Since the mapping uses "$.confirmation_number", "$.appointment_time",
  // and "$.provider_name", these fields must be at the root of the JSON.
  //
  // After receiving this response, the agent can say something like:
  //   "Your appointment is confirmed! Your confirmation number is
  //    BK-482901. You are scheduled for March 20th at 10 AM with
  //    Dr. Sarah Chen."
  res.json({
    success: true,
    confirmation_number: confirmationNumber,
    appointment_time: appointment.appointment_time,
    provider_name: appointment.provider_name,
    service: appointment.service,
    message: "Appointment booked successfully",
  });
});

// ---------------------------------------------------------------------------
// Endpoint 2: Customer Lookup
// POST /api/lookup
//
// Bland's agent calls this to retrieve customer information so it can
// personalize the conversation. The agent extracts a phone number or
// email from the conversation and sends it here.
//
// Expected request body:
// {
//   "phone_number": "+15551234567",
//   "email": "john@example.com"
// }
//
// The response must include fields that match the JSONPath expressions
// defined in the tool's "response" mapping:
//   "customer_name":  "$.name"            -> top-level "name" field
//   "account_plan":   "$.plan"            -> top-level "plan" field
//   "account_status": "$.account_status"  -> top-level "account_status" field
//   "last_visit":     "$.last_visit"      -> top-level "last_visit" field
//
// After this endpoint returns, the agent can say:
//   "Hi John! I can see you're on our Premium plan. Your last visit
//    was on February 15th. How can I help you today?"
// ---------------------------------------------------------------------------
app.post("/api/lookup", (req, res) => {
  const { phone_number, email } = req.body;

  console.log("\n--- Customer Lookup ---");
  console.log("Phone:", phone_number);
  console.log("Email:", email);

  // Try to find the customer by phone number first. If no match is found,
  // fall back to a generic "first time caller" response. In production,
  // you would also search by email and query a real database.
  const customer = mockCustomers[phone_number] || {
    name: "Valued Customer",
    email: email || "N/A",
    plan: "Standard",
    account_status: "Active",
    last_visit: "First time caller",
  };

  console.log("Found:", customer.name);
  console.log("-----------------------\n");

  // Return the customer data directly at the root level, matching
  // the JSONPath expressions in the tool's response mapping.
  // For example, "$.name" maps to the "name" field here.
  res.json(customer);
});

// ---------------------------------------------------------------------------
// Endpoint 3: List All Appointments (for verification)
// GET /api/appointments
//
// This is a convenience endpoint for testing. After a call, you can check
// what appointments were booked by visiting this URL in your browser or
// calling it with curl:
//   curl http://localhost:3001/api/appointments
// ---------------------------------------------------------------------------
app.get("/api/appointments", (req, res) => {
  res.json({ appointments, total: appointments.length });
});

// ---------------------------------------------------------------------------
// Health check endpoint
// GET /health
//
// Use this to verify your server is running and reachable. When you set up
// ngrok, visiting the ngrok URL + /health in your browser should return
// a JSON response with status "ok".
// ---------------------------------------------------------------------------
app.get("/health", (req, res) => {
  res.json({ status: "ok", uptime: process.uptime() });
});

// ---------------------------------------------------------------------------
// Start the server.
// ---------------------------------------------------------------------------
const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`Webhook server running on port ${PORT}`);
  console.log(`\nEndpoints:`);
  console.log(`  POST /api/book           - Book an appointment`);
  console.log(`  POST /api/lookup         - Look up customer info`);
  console.log(`  GET  /api/appointments   - View all bookings`);
  console.log(`  GET  /health             - Health check`);
  console.log(`\nTip: Use ngrok to expose this server to the internet:`);
  console.log(`  npx ngrok http ${PORT}`);
});
