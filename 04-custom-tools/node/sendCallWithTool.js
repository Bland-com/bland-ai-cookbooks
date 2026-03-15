// Send a Call with Custom Tools - Node.js
// This script sends a Bland AI phone call with inline custom tools
// that let the agent interact with external APIs during the conversation.

const axios = require("axios");
require("dotenv").config();

// Your Bland API key from https://app.bland.ai
const API_KEY = process.env.BLAND_API_KEY;
// The phone number to call (E.164 format)
const PHONE_NUMBER = process.env.PHONE_NUMBER;
// Your webhook server URL where the tools will send requests
const WEBHOOK_URL = process.env.WEBHOOK_URL || "https://your-server.com";

async function sendCallWithTools() {
  // Define the custom tools the agent can use during the call.
  // Each tool specifies an external API the agent can call when needed.
  const tools = [
    {
      // Tool 1: Book an appointment
      // The agent will use this when the caller wants to schedule something.
      name: "book_appointment",
      description:
        "Book an appointment for the caller at a specific date, time, and service type. Use this when the caller has confirmed their preferred date, time, and service.",
      url: `${WEBHOOK_URL}/api/book`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: {
        date: "{{input.date}}",
        time: "{{input.time}}",
        service: "{{input.service}}",
        customer_name: "{{input.customer_name}}",
        customer_phone: "{{input.customer_phone}}",
      },
      // The input_schema tells the agent what data to extract from the conversation.
      // The "example" field helps the agent understand the expected format.
      input_schema: {
        example: {
          date: "2026-03-20",
          time: "10:00 AM",
          service: "Dental Checkup",
          customer_name: "John Smith",
          customer_phone: "+15551234567",
        },
        type: "object",
        properties: {
          date: {
            type: "string",
            description: "The appointment date in YYYY-MM-DD format",
          },
          time: {
            type: "string",
            description: "The appointment time, like '10:00 AM' or '2:30 PM'",
          },
          service: {
            type: "string",
            description: "The type of service requested (e.g., Dental Checkup, Teeth Cleaning)",
          },
          customer_name: {
            type: "string",
            description: "The full name of the caller",
          },
          customer_phone: {
            type: "string",
            description: "The caller's phone number",
          },
        },
      },
      // Map fields from the API response to variables the agent can reference.
      // These use JSONPath syntax to extract nested values.
      response: {
        confirmation_number: "$.confirmation_number",
        appointment_time: "$.appointment_time",
        provider_name: "$.provider_name",
      },
      // What the agent says while waiting for the API to respond.
      speech: "Let me book that appointment for you right now. One moment please.",
    },
    {
      // Tool 2: Look up customer information
      // The agent uses this to personalize the conversation.
      name: "lookup_customer",
      description:
        "Look up a customer's account information by their phone number or email. Use this at the start of the call to personalize the experience.",
      url: `${WEBHOOK_URL}/api/lookup`,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: {
        phone_number: "{{input.phone_number}}",
        email: "{{input.email}}",
      },
      input_schema: {
        example: {
          phone_number: "+15551234567",
          email: "john@example.com",
        },
        type: "object",
        properties: {
          phone_number: {
            type: "string",
            description: "The customer's phone number",
          },
          email: {
            type: "string",
            description: "The customer's email address",
          },
        },
      },
      response: {
        customer_name: "$.name",
        account_plan: "$.plan",
        account_status: "$.account_status",
        last_visit: "$.last_visit",
      },
      speech: "Let me pull up your account information real quick.",
    },
  ];

  try {
    const response = await axios.post(
      "https://api.bland.ai/v1/calls",
      {
        phone_number: PHONE_NUMBER,
        // The task prompt tells the agent how to behave and when to use tools.
        task: `You are a friendly receptionist at Bright Smile Dental office.

Your responsibilities:
1. Greet the caller warmly
2. Look up their account using the lookup_customer tool with their phone number
3. If you find their account, greet them by name and reference their last visit
4. Ask how you can help them today
5. If they want to book an appointment:
   - Ask what service they need (cleaning, checkup, whitening, filling, etc.)
   - Ask for their preferred date and time
   - Use the book_appointment tool to schedule it
   - Read back the confirmation number and appointment details
6. If their request is something you cannot handle, offer to transfer them

Always be warm, professional, and efficient. Speak naturally and conversationally.
Do not rush the caller. Confirm details before booking.`,
        voice: "maya",
        model: "base",
        first_sentence: "Hi there! Thank you for calling Bright Smile Dental. How can I help you today?",
        max_duration: 10,
        record: true,
        // Pass the tools array so the agent can use them during the call
        tools: tools,
        // Temperature controls how creative/random the agent's responses are.
        // 0.7 is a good balance of natural conversation and consistency.
        temperature: 0.7,
        // The interruption_threshold controls how patient the agent is.
        // 150 gives the caller enough time to provide detailed info like dates.
        interruption_threshold: 150,
      },
      {
        headers: {
          Authorization: API_KEY,
          "Content-Type": "application/json",
        },
      }
    );

    console.log("Call sent successfully!");
    console.log("Call ID:", response.data.call_id);
    console.log("Status:", response.data.status);
    console.log("\nThe agent will use the booking and lookup tools during the call.");
    console.log("Make sure your webhook server is running at:", WEBHOOK_URL);
  } catch (error) {
    console.error("Error sending call:", error.response?.data || error.message);
  }
}

sendCallWithTools();
