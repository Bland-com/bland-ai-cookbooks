"""
Bland AI - List Available Voices (Python)

This script fetches all available voices from the Bland AI API and displays
them in a formatted table. It also filters for "Bland Curated" voices,
which are recommended for the best phone call audio quality.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python list_voices.py

The script will:
    - Fetch the complete voice catalog from the API
    - Display all voices in a readable table
    - Show a filtered list of Bland Curated voices
    - Print voice details including name, description, tags, and rating
"""

import os
import sys

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
# This keeps your API key out of source control.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
API_KEY = os.getenv("BLAND_API_KEY")

# The Bland API base URL. All endpoints are under this path.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Fetch voices from the API
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
}

print("Fetching available voices from Bland AI...")
print()

try:
    # Make the GET request to the List Voices endpoint.
    # This returns an array of voice objects with details like name,
    # description, tags, and ratings.
    response = requests.get(
        "{}/voices".format(BASE_URL),
        headers=headers,
        timeout=30,  # 30-second timeout for the HTTP request
    )

    # Raise an exception for HTTP error codes (4xx, 5xx).
    response.raise_for_status()

except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the Bland API.")
    print("Check your internet connection and try again.")
    sys.exit(1)

except requests.exceptions.Timeout:
    print("Error: The request timed out.")
    print("The Bland API may be experiencing high traffic. Try again in a moment.")
    sys.exit(1)

except requests.exceptions.HTTPError:
    print("Error: API returned status code {}.".format(response.status_code))
    print("Response: {}".format(response.text))
    sys.exit(1)

# Parse the JSON response. The API returns an array of voice objects.
voices = response.json()

# ---------------------------------------------------------------------------
# Helper function: format a table row
# ---------------------------------------------------------------------------


def print_table_row(name, description, tags_str, rating_str):
    """Print a single row of the voice table with consistent column widths.

    Args:
        name: The voice name (column 1, 15 chars wide).
        description: Short voice description (column 2, 30 chars wide).
        tags_str: Comma-separated tags (column 3, 35 chars wide).
        rating_str: Average rating display (column 4, 10 chars wide).
    """
    print(
        "  {:<15} {:<30} {:<35} {:<10}".format(
            name[:15],          # Truncate name to fit column
            description[:30],   # Truncate description to fit column
            tags_str[:35],      # Truncate tags to fit column
            rating_str[:10],    # Truncate rating to fit column
        )
    )


def print_table_separator():
    """Print a horizontal line to separate table sections."""
    print("  " + "-" * 94)


# ---------------------------------------------------------------------------
# Display all voices
# ---------------------------------------------------------------------------

# Check if we received any voices.
if not voices:
    print("No voices found. This may indicate an API issue.")
    sys.exit(1)

print("Found {} voice(s) available on your account:".format(len(voices)))
print()

# Print the table header.
print_table_row("NAME", "DESCRIPTION", "TAGS", "RATING")
print_table_separator()

# Iterate through each voice and display its details.
for voice in voices:
    # Extract the voice name. This is the value you pass to the "voice"
    # parameter when creating a persona or sending a call.
    name = voice.get("name", "Unknown")

    # The description gives a brief summary of the voice characteristics,
    # such as "Young American Female" or "British Male".
    description = voice.get("description", "No description")

    # Tags are descriptive labels that include language, quality indicators,
    # and other metadata. Look for "Bland Curated" to find recommended voices.
    tags = voice.get("tags", [])
    tags_str = ", ".join(tags) if tags else "No tags"

    # Rating information helps you gauge voice quality based on user feedback.
    # average_rating is the mean score and total_ratings is the number of reviews.
    avg_rating = voice.get("average_rating", 0)
    total_ratings = voice.get("total_ratings", 0)

    # Format the rating as "X.X (N)" where X.X is the average and N is the count.
    if total_ratings > 0:
        rating_str = "{:.1f} ({})".format(avg_rating, total_ratings)
    else:
        rating_str = "No ratings"

    print_table_row(name, description, tags_str, rating_str)

# ---------------------------------------------------------------------------
# Filter and display Bland Curated voices
# ---------------------------------------------------------------------------

# Bland Curated voices have been optimized for phone call audio quality.
# They are tagged with "Bland Curated" in their tags array.
# These are the recommended starting point for most use cases.
curated_voices = [
    v for v in voices
    if any("curated" in tag.lower() for tag in v.get("tags", []))
]

print()
print("=" * 98)
print()

if curated_voices:
    print(
        "Bland Curated Voices ({} found):".format(len(curated_voices))
    )
    print("These voices are optimized for phone call quality and recommended")
    print("as the best starting point for most use cases.")
    print()
    print_table_row("NAME", "DESCRIPTION", "TAGS", "RATING")
    print_table_separator()

    for voice in curated_voices:
        name = voice.get("name", "Unknown")
        description = voice.get("description", "No description")
        tags = voice.get("tags", [])
        tags_str = ", ".join(tags) if tags else "No tags"
        avg_rating = voice.get("average_rating", 0)
        total_ratings = voice.get("total_ratings", 0)

        if total_ratings > 0:
            rating_str = "{:.1f} ({})".format(avg_rating, total_ratings)
        else:
            rating_str = "No ratings"

        print_table_row(name, description, tags_str, rating_str)
else:
    print("No Bland Curated voices found in the catalog.")
    print("All voices listed above are still available for use.")

# ---------------------------------------------------------------------------
# Usage tips
# ---------------------------------------------------------------------------

print()
print("=" * 98)
print()
print("How to use a voice:")
print('  1. Copy the NAME of the voice you want (e.g., "maya", "ryan").')
print("  2. Pass it as the \"voice\" parameter when creating a persona or sending a call.")
print("  3. Test a few voices with short calls to find the best fit for your use case.")
print()
print("Popular voices for phone calls: Maya, Ryan, Mason, Tina, Josh, Florian,")
print("Derek, June, Nat, Paige")
