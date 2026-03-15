/**
 * listNumbers.js
 * ==============
 * List all inbound phone numbers on your Bland AI account.
 *
 * This script sends a GET request to retrieve every inbound number you own,
 * along with its current configuration (prompt, voice, transfer rules, etc.).
 * Use it to verify that your numbers are set up correctly or to get a quick
 * overview of your inbound infrastructure.
 *
 * Usage:
 *   1. Copy .env.example to .env and add your API key.
 *   2. Run: node listNumbers.js
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
const API_KEY = process.env.BLAND_API_KEY;

// The Bland AI API endpoint for listing all inbound numbers.
const LIST_URL = "https://api.bland.ai/v1/inbound";

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

async function listNumbers() {
  // Verify the API key is set before making the request.
  if (!API_KEY) {
    console.log("Error: BLAND_API_KEY is not set.");
    console.log("Copy .env.example to .env and add your API key.");
    return null;
  }

  // Build request headers with the API key.
  const headers = {
    Authorization: API_KEY,
  };

  console.log("Fetching your inbound phone numbers...");
  console.log(`Request URL: ${LIST_URL}`);
  console.log();

  try {
    // Send the GET request. No body or query parameters are needed.
    const response = await axios.get(LIST_URL, { headers });

    // axios puts the parsed JSON body in response.data.
    const data = response.data;

    // The response should be a list (or contain a list) of numbers.
    // We handle both cases: a raw array or an object with a key containing
    // the array.
    const numbers = Array.isArray(data) ? data : data.numbers || data;

    if (Array.isArray(numbers) && numbers.length === 0) {
      console.log("You have no inbound numbers yet.");
      console.log("Run purchaseNumber.js to buy your first number.");
    } else if (Array.isArray(numbers)) {
      console.log(`Found ${numbers.length} inbound number(s):\n`);

      numbers.forEach((numberConfig, index) => {
        // Extract key fields for the summary display.
        const phone = numberConfig.phone_number || "Unknown";
        const voice = numberConfig.voice || "Not set";
        const model = numberConfig.model || "Not set";
        let promptPreview = numberConfig.prompt || "";

        // Show just the first 80 characters of the prompt so the output
        // stays readable. You can log the full config by uncommenting the
        // JSON.stringify line below.
        if (promptPreview.length > 80) {
          promptPreview = promptPreview.substring(0, 80) + "...";
        }

        console.log(`  [${index + 1}] ${phone}`);
        console.log(`      Voice: ${voice}`);
        console.log(`      Model: ${model}`);
        console.log(`      Prompt: ${promptPreview}`);

        // Check for transfer configuration.
        const transferList = numberConfig.transfer_list;
        if (transferList && typeof transferList === "object") {
          const departments = Object.keys(transferList);
          console.log(`      Transfers: ${departments.join(", ")}`);
        }

        console.log();
      });

      // Uncomment the line below to see the full raw JSON response
      // for debugging or detailed inspection.
      // console.log(JSON.stringify(numbers, null, 2));
    } else {
      // If the response is not an array, print it as-is for debugging.
      console.log("Response:");
      console.log(JSON.stringify(data, null, 2));
    }

    return data;
  } catch (error) {
    // axios throws an error for non-2xx status codes.
    if (error.response) {
      console.log(`Error: Received status code ${error.response.status}`);
      console.log(JSON.stringify(error.response.data, null, 2));
    } else {
      console.log(`Request failed: ${error.message}`);
    }
    return null;
  }
}

// Run the function.
listNumbers();
