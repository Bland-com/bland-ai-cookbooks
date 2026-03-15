/**
 * purchaseNumber.js
 * =================
 * Buy an inbound phone number from Bland AI.
 *
 * This script sends a POST request to the Bland AI API to purchase a new
 * phone number. Once purchased, the number costs $15/month and will appear
 * on your account. You can then configure an AI agent to answer calls on
 * this number using configureInbound.js.
 *
 * Usage:
 *   1. Copy .env.example to .env and add your API key.
 *   2. (Optional) Change AREA_CODE or COUNTRY_CODE below.
 *   3. Run: node purchaseNumber.js
 *
 * Dependencies:
 *   npm install axios dotenv
 */

const axios = require("axios");
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland AI API key, loaded from the .env file.
// If you prefer, you can paste it directly here (not recommended for security).
const API_KEY = process.env.BLAND_API_KEY;

// The Bland AI API endpoint for purchasing inbound numbers.
const PURCHASE_URL = "https://api.bland.ai/v1/inbound/purchase";

// Three-digit area code for the new number. Change this to any valid US or
// Canadian area code. Common examples:
//   "415" = San Francisco, CA
//   "212" = New York, NY
//   "312" = Chicago, IL
//   "737" = Austin, TX
//   "416" = Toronto, ON (Canada)
const AREA_CODE = "415";

// Country code. Bland AI currently supports:
//   "US" = United States
//   "CA" = Canada
const COUNTRY_CODE = "US";

// (Optional) If you want a specific phone number, set it here in the format
// "+12223334444". Leave as null to let Bland pick an available number for you.
const SPECIFIC_NUMBER = null;

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function purchaseNumber() {
  // Verify the API key is set before making the request.
  if (!API_KEY) {
    console.log("Error: BLAND_API_KEY is not set.");
    console.log("Copy .env.example to .env and add your API key.");
    return null;
  }

  // Build the request headers. Bland AI uses the raw API key in the
  // Authorization header (no "Bearer" prefix).
  const headers = {
    Authorization: API_KEY,
    "Content-Type": "application/json",
  };

  // Build the request body with the desired area code and country.
  const payload = {
    area_code: AREA_CODE,
    country_code: COUNTRY_CODE,
  };

  // If a specific number was requested, include it in the payload.
  // The API will attempt to purchase that exact number if it is available.
  if (SPECIFIC_NUMBER) {
    payload.phone_number = SPECIFIC_NUMBER;
  }

  console.log(
    `Purchasing a phone number with area code ${AREA_CODE} (${COUNTRY_CODE})...`
  );
  console.log(`Request URL: ${PURCHASE_URL}`);
  console.log(`Payload: ${JSON.stringify(payload, null, 2)}`);
  console.log();

  try {
    // Send the POST request to the Bland AI purchase endpoint.
    const response = await axios.post(PURCHASE_URL, payload, { headers });

    // axios puts the parsed JSON body in response.data.
    const data = response.data;

    console.log("Success! Phone number purchased.");
    console.log(JSON.stringify(data, null, 2));
    console.log();
    console.log("Next step: Copy the phone number from the response above");
    console.log(
      "and paste it into configureInbound.js as the INBOUND_NUMBER."
    );

    return data;
  } catch (error) {
    // axios throws an error for non-2xx status codes.
    if (error.response) {
      // The server responded with an error status code.
      console.log(`Error: Received status code ${error.response.status}`);
      console.log(JSON.stringify(error.response.data, null, 2));
    } else {
      // Network error, timeout, or other issue.
      console.log(`Request failed: ${error.message}`);
    }
    return null;
  }
}

// Run the function.
purchaseNumber();
