/**
 * listPathways.js
 *
 * Lists all pathways on your Bland AI account. Useful for finding pathway IDs,
 * checking what pathways exist, and verifying that a newly created pathway
 * shows up correctly.
 *
 * Usage:
 *   1. Copy .env.example to .env and fill in your API key
 *   2. npm install axios dotenv
 *   3. node listPathways.js
 */

const axios = require("axios");
require("dotenv").config();

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland AI API key
const BLAND_API_KEY = process.env.BLAND_API_KEY;

// Base URL and headers for the Bland API
const BASE_URL = "https://api.bland.ai/v1";
const HEADERS = {
  Authorization: BLAND_API_KEY,
  "Content-Type": "application/json",
};

/**
 * Retrieve all pathways on your account.
 *
 * GET https://api.bland.ai/v1/pathway
 * Headers: { Authorization: "YOUR_API_KEY" }
 *
 * Returns a list of pathway objects. Each pathway includes its ID, name,
 * description, and metadata. The node/edge structure is not included in
 * the list response; you need to fetch individual pathways for that.
 */
async function listPathways() {
  const url = `${BASE_URL}/pathway`;

  console.log("Fetching pathways...");
  const response = await axios.get(url, { headers: HEADERS });

  const data = response.data;

  // The response structure may vary. Handle both list and object formats.
  // Some endpoints return the list directly, others wrap it in a key.
  let pathways;
  if (Array.isArray(data)) {
    pathways = data;
  } else if (typeof data === "object" && data !== null) {
    // Try common wrapper keys
    pathways = data.pathways || data.data || [data];
  } else {
    pathways = [];
  }

  if (!pathways || pathways.length === 0) {
    console.log("No pathways found on this account.");
    console.log("Run createPathway.js to create your first pathway.");
    return;
  }

  // Print a formatted summary of each pathway
  console.log(`\nFound ${pathways.length} pathway(s):\n`);
  console.log("-".repeat(70));

  pathways.forEach((pathway, index) => {
    // Extract common fields. Field names may vary by API version.
    const pathwayId = pathway.pathway_id || pathway.id || "N/A";
    const name = pathway.name || "Unnamed";
    const description = pathway.description || "No description";
    const createdAt = pathway.created_at || pathway.createdAt || "N/A";

    console.log(`  ${index + 1}. ${name}`);
    console.log(`     ID:          ${pathwayId}`);
    console.log(`     Description: ${description}`);
    console.log(`     Created:     ${createdAt}`);
    console.log();
  });

  console.log("-".repeat(70));

  // Also print the raw JSON for reference
  console.log(`\nRaw JSON response:\n${JSON.stringify(data, null, 2)}`);

  return data;
}

/**
 * Validate the API key and list all pathways.
 */
async function main() {
  if (!BLAND_API_KEY) {
    console.error("Error: BLAND_API_KEY is not set.");
    console.error("Copy .env.example to .env and add your API key.");
    return;
  }

  try {
    await listPathways();
  } catch (error) {
    // Axios errors include the response data which often has helpful details
    if (error.response) {
      console.error(`API Error (${error.response.status}):`);
      console.error(JSON.stringify(error.response.data, null, 2));
    } else {
      console.error("Error:", error.message);
    }
  }
}

main();
