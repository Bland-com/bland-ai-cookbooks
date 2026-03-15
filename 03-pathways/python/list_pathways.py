"""
list_pathways.py

Lists all pathways on your Bland AI account. Useful for finding pathway IDs,
checking what pathways exist, and verifying that a newly created pathway
shows up correctly.

Usage:
  1. Copy .env.example to .env and fill in your API key
  2. pip install requests python-dotenv
  3. python list_pathways.py
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory
load_dotenv()

# Your Bland AI API key
BLAND_API_KEY = os.getenv("BLAND_API_KEY")

# Base URL and headers for the Bland API
BASE_URL = "https://api.bland.ai/v1"
HEADERS = {
    "Authorization": BLAND_API_KEY,
    "Content-Type": "application/json",
}


def list_pathways():
    """
    Retrieve all pathways on your account.

    GET https://api.bland.ai/v1/pathway
    Headers: { "Authorization": "YOUR_API_KEY" }

    Returns a list of pathway objects. Each pathway includes its ID, name,
    description, and metadata. The node/edge structure is not included in
    the list response; you need to fetch individual pathways for that.
    """
    url = f"{BASE_URL}/pathway"

    print("Fetching pathways...")
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    data = response.json()

    # The response structure may vary. Handle both list and object formats.
    # Some endpoints return the list directly, others wrap it in a key.
    if isinstance(data, list):
        pathways = data
    elif isinstance(data, dict):
        # Try common wrapper keys
        pathways = data.get("pathways", data.get("data", [data]))
    else:
        pathways = []

    if not pathways:
        print("No pathways found on this account.")
        print("Run create_pathway.py to create your first pathway.")
        return

    # Print a formatted summary of each pathway
    print(f"\nFound {len(pathways)} pathway(s):\n")
    print("-" * 70)

    for i, pathway in enumerate(pathways, start=1):
        # Extract common fields. Field names may vary by API version.
        pathway_id = pathway.get("pathway_id", pathway.get("id", "N/A"))
        name = pathway.get("name", "Unnamed")
        description = pathway.get("description", "No description")
        created_at = pathway.get("created_at", pathway.get("createdAt", "N/A"))

        print(f"  {i}. {name}")
        print(f"     ID:          {pathway_id}")
        print(f"     Description: {description}")
        print(f"     Created:     {created_at}")
        print()

    print("-" * 70)

    # Also print the raw JSON for reference
    print(f"\nRaw JSON response:\n{json.dumps(data, indent=2)}")

    return data


def main():
    """
    Validate the API key and list all pathways.
    """
    if not BLAND_API_KEY:
        print("Error: BLAND_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return

    list_pathways()


if __name__ == "__main__":
    main()
