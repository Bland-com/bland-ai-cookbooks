/**
 * Calendar API Server - Node.js (Express)
 *
 * Simulates a calendar/booking system that Bland AI custom tools can
 * interact with. The scheduling agent calls these endpoints during live
 * phone calls to check availability and book appointments.
 *
 * Run this server locally, then expose it with ngrok so Bland can reach it:
 *    npm install express cors
 *    node calendarServer.js
 *    npx ngrok http 3001
 */

const express = require("express");
const cors = require("cors");

// ---------------------------------------------------------------------------
// Express app setup
// ---------------------------------------------------------------------------

// Create the Express application instance.
const app = express();

// Enable CORS for all origins. This allows the Bland API servers (or any
// origin) to make requests to these endpoints without being blocked by
// the browser's same-origin policy. In production, you would restrict
// this to specific origins.
app.use(cors());

// Parse incoming JSON request bodies. This is required because the Bland
// AI tool system sends all tool requests as JSON POST bodies.
app.use(express.json());

// ---------------------------------------------------------------------------
// In-memory storage for appointments (use a real database in production)
// ---------------------------------------------------------------------------

// This array holds all booked appointments for the current server session.
// When the server restarts, all bookings are lost. In a production system,
// you would store these in a database like PostgreSQL, MySQL, or MongoDB.
const bookedAppointments = [];

// ---------------------------------------------------------------------------
// Available time slots
// ---------------------------------------------------------------------------

// The complete set of appointment slots for every day. In a real application,
// you would check this against a live calendar system (Google Calendar,
// Calendly, etc.) rather than using a static list.
const ALL_SLOTS = [
  "9:00 AM",
  "9:30 AM",
  "10:00 AM",
  "10:30 AM",
  "11:00 AM",
  "11:30 AM",
  "1:00 PM",
  "1:30 PM",
  "2:00 PM",
  "2:30 PM",
  "3:00 PM",
  "3:30 PM",
  "4:00 PM",
  "4:30 PM",
];

// ---------------------------------------------------------------------------
// Helper: seeded random number generator
// ---------------------------------------------------------------------------

/**
 * Simple seeded pseudo-random number generator.
 * Uses the same approach as the Python version so that the same date
 * string produces the same "booked" slots, making testing predictable.
 *
 * @param {number} seed - An integer seed value.
 * @returns {function} A function that returns a pseudo-random float in [0, 1).
 */
function seededRandom(seed) {
  // Use a linear congruential generator (LCG) with commonly used constants.
  // This is not cryptographically secure, but it is plenty for simulating
  // random bookings in a demo server.
  let state = seed;
  return function () {
    // LCG formula: state = (a * state + c) % m
    state = (state * 1664525 + 1013904223) & 0x7fffffff;
    return state / 0x7fffffff;
  };
}

/**
 * Compute a numeric seed from a string by summing the character codes.
 * This mirrors the Python version: sum(ord(c) for c in str(date)).
 *
 * @param {string} str - The input string (typically a date like "2026-03-20").
 * @returns {number} A positive integer seed.
 */
function stringSeed(str) {
  let total = 0;
  for (let i = 0; i < str.length; i++) {
    total += str.charCodeAt(i);
  }
  return total;
}

// ---------------------------------------------------------------------------
// POST /api/availability - Check available appointment slots
// ---------------------------------------------------------------------------

app.post("/api/availability", (req, res) => {
  /**
   * Check available appointment slots for a given date and service.
   * The Bland AI agent calls this tool when a caller asks about availability.
   *
   * Expected body: { "date": "2026-03-20", "service": "Teeth Cleaning" }
   * Returns: { "available_slots": [...], "provider_name": "..." }
   */

  // Extract the date and service from the request body. Default to safe
  // fallback values if they are missing so the endpoint never crashes.
  const date = req.body.date || "unspecified";
  const service = req.body.service || "General Checkup";

  console.log();
  console.log("--- Availability Check ---");
  console.log(`Date: ${date}`);
  console.log(`Service: ${service}`);

  // Simulate some slots being taken based on the date string.
  // Use the date as a seed so results are consistent for the same date.
  const seed = stringSeed(String(date));
  const rng = seededRandom(seed);

  // Decide how many slots to mark as booked (between 3 and 6).
  const numBooked = 3 + Math.floor(rng() * 4);

  // Pick which slot indices are "booked" by shuffling indices and taking
  // the first numBooked entries. We use a Fisher-Yates-style partial
  // shuffle seeded by our RNG.
  const indices = ALL_SLOTS.map((_, i) => i);
  for (let i = indices.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    const temp = indices[i];
    indices[i] = indices[j];
    indices[j] = temp;
  }
  const bookedIndices = new Set(indices.slice(0, numBooked));

  // Build the list of available slots by excluding booked indices.
  let available = ALL_SLOTS.filter((_, i) => !bookedIndices.has(i));

  // Also remove any slots that have been actually booked in this session.
  // This ensures that if an agent books a slot during the call, it does
  // not appear as available again in subsequent availability checks.
  for (const appt of bookedAppointments) {
    if (appt.date === date && available.includes(appt.time)) {
      available = available.filter((slot) => slot !== appt.time);
    }
  }

  // Assign a provider based on the service type. In a real application,
  // you would look up provider schedules in your database.
  const dentalServices = [
    "cleaning",
    "teeth cleaning",
    "checkup",
    "dental checkup",
  ];
  const provider = dentalServices.includes(service.toLowerCase())
    ? "Dr. Sarah Chen"
    : "Dr. James Wilson";

  console.log(`Available slots: ${available.length}`);
  console.log(`Provider: ${provider}`);
  console.log("--------------------------");
  console.log();

  // Return the availability data to the Bland AI agent. The agent reads
  // the "available_slots" and "provider_name" fields using the response
  // mapping defined in the tool configuration.
  return res.json({
    available_slots: available,
    provider_name: provider,
    date: date,
    service: service,
  });
});

// ---------------------------------------------------------------------------
// POST /api/book - Book an appointment
// ---------------------------------------------------------------------------

app.post("/api/book", (req, res) => {
  /**
   * Book an appointment at a specific date, time, and service.
   * The Bland AI agent calls this after the caller confirms their choice.
   *
   * Expected body: { "date": "...", "time": "...", "service": "...",
   *                   "customer_name": "...", "customer_phone": "..." }
   * Returns: { "success": true, "confirmation_number": "BK-123456", ... }
   */

  // Extract all booking fields from the request body.
  const date = req.body.date || "TBD";
  const timeSlot = req.body.time || "TBD";
  const service = req.body.service || "General Checkup";
  const customerName = req.body.customer_name || "Guest";
  const customerPhone = req.body.customer_phone || "N/A";

  console.log();
  console.log("--- Booking Request ---");
  console.log(`Customer: ${customerName}`);
  console.log(`Phone: ${customerPhone}`);
  console.log(`Service: ${service}`);
  console.log(`Date: ${date} at ${timeSlot}`);

  // Generate a 6-digit confirmation number. In production, use a UUID or
  // database-generated ID to guarantee uniqueness.
  const digits = Math.floor(100000 + Math.random() * 900000);
  const confNumber = `BK-${digits}`;

  // Assign a provider based on the service type.
  const dentalServices = [
    "cleaning",
    "teeth cleaning",
    "checkup",
    "dental checkup",
  ];
  const provider = dentalServices.includes(service.toLowerCase())
    ? "Dr. Sarah Chen"
    : "Dr. James Wilson";

  // Build the appointment record and store it in memory.
  const appointment = {
    confirmation_number: confNumber,
    customer_name: customerName,
    customer_phone: customerPhone,
    service: service,
    date: date,
    time: timeSlot,
    appointment_time: `${date} at ${timeSlot}`,
    provider_name: provider,
    created_at: new Date().toISOString(),
  };

  bookedAppointments.push(appointment);

  console.log(`Confirmation: ${confNumber}`);
  console.log(`Provider: ${provider}`);
  console.log("----------------------");
  console.log();

  // Return the booking confirmation. The agent reads "confirmation_number",
  // "appointment_time", and "provider_name" to relay back to the caller.
  return res.json({
    success: true,
    confirmation_number: confNumber,
    appointment_time: `${date} at ${timeSlot}`,
    provider_name: provider,
    service: service,
    message: "Appointment booked successfully",
  });
});

// ---------------------------------------------------------------------------
// GET /api/appointments - List all booked appointments
// ---------------------------------------------------------------------------

app.get("/api/appointments", (req, res) => {
  /**
   * List all booked appointments (for verification purposes).
   * This endpoint is not called by the Bland AI agent; it exists so you
   * can manually verify bookings in your browser or with curl.
   */
  return res.json({
    appointments: bookedAppointments,
    total: bookedAppointments.length,
  });
});

// ---------------------------------------------------------------------------
// GET /health - Health check
// ---------------------------------------------------------------------------

app.get("/health", (req, res) => {
  /**
   * Simple health check endpoint. Returns a 200 OK status to confirm
   * the server is running. Useful for verifying the server is up before
   * starting the scheduling agent.
   */
  return res.json({ status: "ok" });
});

// ---------------------------------------------------------------------------
// Start the server
// ---------------------------------------------------------------------------

// Use port 3001 to avoid conflicts with other cookbook servers (the webhook
// listener in cookbook 10 uses port 3000 by default).
const PORT = process.env.PORT || 3001;

app.listen(PORT, () => {
  console.log("Calendar API Server (Node.js)");
  console.log();
  console.log("Endpoints:");
  console.log("  POST /api/availability  - Check available slots");
  console.log("  POST /api/book          - Book an appointment");
  console.log("  GET  /api/appointments  - List all bookings");
  console.log("  GET  /health            - Health check");
  console.log();
  console.log(`Listening on port ${PORT}`);
  console.log();
  console.log("Tip: Expose with ngrok:");
  console.log(`  npx ngrok http ${PORT}`);
  console.log();
});
