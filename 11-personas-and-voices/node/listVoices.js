/**
 * Bland AI - List Available Voices (Node.js)
 *
 * This script fetches all available voices from the Bland AI API and displays
 * them in a formatted table. It also filters for "Bland Curated" voices,
 * which are recommended for the best phone call audio quality.
 *
 * Usage:
 *    1. Copy .env.example to .env and fill in your API key.
 *    2. Install dependencies: npm install axios dotenv
 *    3. Run: node listVoices.js
 *
 * The script will:
 *    - Fetch the complete voice catalog from the API
 *    - Display all voices in a readable table
 *    - Show a filtered list of Bland Curated voices
 *    - Print voice details including name, description, tags, and rating
 */

// Load environment variables from the .env file in this directory.
// This keeps your API key out of source control.
require("dotenv").config();
const axios = require("axios");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
const API_KEY = process.env.BLAND_API_KEY;

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

// ---------------------------------------------------------------------------
// Helper functions for table formatting
// ---------------------------------------------------------------------------

/**
 * Pad or truncate a string to a fixed width for table alignment.
 *
 * @param {string} str - The string to format.
 * @param {number} width - The desired column width.
 * @returns {string} The padded or truncated string.
 */
function padColumn(str, width) {
  // Convert to string in case a non-string value is passed.
  const text = String(str);

  // Truncate if longer than the column width.
  if (text.length > width) {
    return text.substring(0, width);
  }

  // Pad with spaces if shorter than the column width.
  return text + " ".repeat(width - text.length);
}

/**
 * Print a single row of the voice table with consistent column widths.
 *
 * @param {string} name - The voice name (column 1, 15 chars wide).
 * @param {string} description - Short voice description (column 2, 30 chars).
 * @param {string} tagsStr - Comma-separated tags (column 3, 35 chars).
 * @param {string} ratingStr - Average rating display (column 4, 10 chars).
 */
function printTableRow(name, description, tagsStr, ratingStr) {
  console.log(
    `  ${padColumn(name, 15)} ${padColumn(description, 30)} ${padColumn(tagsStr, 35)} ${padColumn(ratingStr, 10)}`
  );
}

/**
 * Print a horizontal line to separate table sections.
 */
function printTableSeparator() {
  console.log("  " + "-".repeat(94));
}

// ---------------------------------------------------------------------------
// Fetch and display voices
// ---------------------------------------------------------------------------

async function listVoices() {
  console.log("Fetching available voices from Bland AI...");
  console.log();

  try {
    // Make the GET request to the List Voices endpoint.
    // This returns an array of voice objects with details like name,
    // description, tags, and ratings.
    const response = await axios.get(`${BASE_URL}/voices`, {
      headers: {
        // Bland uses a simple API key in the Authorization header
        // (no "Bearer" prefix needed).
        Authorization: API_KEY,
      },
      timeout: 30000, // 30-second timeout for the HTTP request
    });

    // The API returns an array of voice objects.
    const voices = response.data;

    // Check if we received any voices.
    if (!voices || !Array.isArray(voices) || voices.length === 0) {
      console.log("No voices found. This may indicate an API issue.");
      process.exit(1);
    }

    // -------------------------------------------------------------------
    // Display all voices in a formatted table
    // -------------------------------------------------------------------

    console.log(`Found ${voices.length} voice(s) available on your account:`);
    console.log();

    // Print the table header.
    printTableRow("NAME", "DESCRIPTION", "TAGS", "RATING");
    printTableSeparator();

    // Iterate through each voice and display its details.
    for (const voice of voices) {
      // Extract the voice name. This is the value you pass to the "voice"
      // parameter when creating a persona or sending a call.
      const name = voice.name || "Unknown";

      // The description gives a brief summary of the voice characteristics,
      // such as "Young American Female" or "British Male".
      const description = voice.description || "No description";

      // Tags are descriptive labels that include language, quality indicators,
      // and other metadata. Look for "Bland Curated" to find recommended voices.
      const tags = voice.tags || [];
      const tagsStr = tags.length > 0 ? tags.join(", ") : "No tags";

      // Rating information helps you gauge voice quality based on user feedback.
      // average_rating is the mean score and total_ratings is the review count.
      const avgRating = voice.average_rating || 0;
      const totalRatings = voice.total_ratings || 0;

      // Format the rating as "X.X (N)" where X.X is the average and N is
      // the total number of ratings.
      const ratingStr =
        totalRatings > 0
          ? `${avgRating.toFixed(1)} (${totalRatings})`
          : "No ratings";

      printTableRow(name, description, tagsStr, ratingStr);
    }

    // -------------------------------------------------------------------
    // Filter and display Bland Curated voices
    // -------------------------------------------------------------------

    // Bland Curated voices have been optimized for phone call audio quality.
    // They are tagged with "Bland Curated" in their tags array.
    // These are the recommended starting point for most use cases.
    const curatedVoices = voices.filter((v) => {
      const tags = v.tags || [];
      // Check if any tag contains "curated" (case-insensitive).
      return tags.some((tag) => tag.toLowerCase().includes("curated"));
    });

    console.log();
    console.log("=".repeat(98));
    console.log();

    if (curatedVoices.length > 0) {
      console.log(`Bland Curated Voices (${curatedVoices.length} found):`);
      console.log(
        "These voices are optimized for phone call quality and recommended"
      );
      console.log("as the best starting point for most use cases.");
      console.log();
      printTableRow("NAME", "DESCRIPTION", "TAGS", "RATING");
      printTableSeparator();

      for (const voice of curatedVoices) {
        const name = voice.name || "Unknown";
        const description = voice.description || "No description";
        const tags = voice.tags || [];
        const tagsStr = tags.length > 0 ? tags.join(", ") : "No tags";
        const avgRating = voice.average_rating || 0;
        const totalRatings = voice.total_ratings || 0;
        const ratingStr =
          totalRatings > 0
            ? `${avgRating.toFixed(1)} (${totalRatings})`
            : "No ratings";

        printTableRow(name, description, tagsStr, ratingStr);
      }
    } else {
      console.log("No Bland Curated voices found in the catalog.");
      console.log("All voices listed above are still available for use.");
    }

    // -------------------------------------------------------------------
    // Usage tips
    // -------------------------------------------------------------------

    console.log();
    console.log("=".repeat(98));
    console.log();
    console.log("How to use a voice:");
    console.log(
      '  1. Copy the NAME of the voice you want (e.g., "maya", "ryan").'
    );
    console.log(
      '  2. Pass it as the "voice" parameter when creating a persona or sending a call.'
    );
    console.log(
      "  3. Test a few voices with short calls to find the best fit for your use case."
    );
    console.log();
    console.log(
      "Popular voices for phone calls: Maya, Ryan, Mason, Tina, Josh, Florian,"
    );
    console.log("Derek, June, Nat, Paige");
  } catch (error) {
    // Handle different types of errors with helpful messages.
    if (error.code === "ECONNREFUSED" || error.code === "ENOTFOUND") {
      console.error("Error: Could not connect to the Bland API.");
      console.error("Check your internet connection and try again.");
    } else if (error.code === "ECONNABORTED") {
      console.error("Error: The request timed out.");
      console.error(
        "The Bland API may be experiencing high traffic. Try again in a moment."
      );
    } else if (error.response) {
      // The API returned an error status code (4xx, 5xx).
      console.error(
        `Error: API returned status code ${error.response.status}.`
      );
      console.error(
        `Response: ${JSON.stringify(error.response.data, null, 2)}`
      );
    } else {
      // Some other unexpected error.
      console.error(`Error: ${error.message}`);
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

listVoices();
