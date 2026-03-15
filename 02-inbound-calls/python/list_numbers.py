"""
list_numbers.py
===============
List all inbound phone numbers on your Bland AI account.

This script sends a GET request to retrieve every inbound number you own,
along with its current configuration (prompt, voice, transfer rules, etc.).
Use it to verify that your numbers are set up correctly or to get a quick
overview of your inbound infrastructure.

Usage:
    1. Copy .env.example to .env and add your API key.
    2. Run: python list_numbers.py

Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from the .env file in this directory.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Your Bland AI API key, loaded from the .env file.
API_KEY = os.getenv("BLAND_API_KEY")

# The Bland AI API endpoint for listing all inbound numbers.
LIST_URL = "https://api.bland.ai/v1/inbound"

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def list_numbers():
    """
    Fetch and display all inbound phone numbers on your Bland AI account.

    Returns the API response as a list of number configuration objects.
    """

    # Verify the API key is set before making the request.
    if not API_KEY:
        print("Error: BLAND_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return None

    # Build request headers with the API key.
    headers = {
        "Authorization": API_KEY,
    }

    print("Fetching your inbound phone numbers...")
    print(f"Request URL: {LIST_URL}")
    print()

    try:
        # Send the GET request. No body or query parameters are needed.
        response = requests.get(LIST_URL, headers=headers)

        # Parse the JSON response.
        data = response.json()

        if response.status_code == 200:
            # The response should be a list (or contain a list) of numbers.
            # The exact structure depends on the API, but we handle both
            # cases: a raw list or an object with a key containing the list.
            numbers = data if isinstance(data, list) else data.get("numbers", data)

            if isinstance(numbers, list) and len(numbers) == 0:
                print("You have no inbound numbers yet.")
                print("Run purchase_number.py to buy your first number.")
            elif isinstance(numbers, list):
                print(f"Found {len(numbers)} inbound number(s):\n")

                for i, number_config in enumerate(numbers, start=1):
                    # Print a summary for each number.
                    phone = number_config.get("phone_number", "Unknown")
                    voice = number_config.get("voice", "Not set")
                    model = number_config.get("model", "Not set")
                    prompt_preview = number_config.get("prompt", "")

                    # Show just the first 80 characters of the prompt so the
                    # output stays readable. You can print the full config
                    # by uncommenting the json.dumps line below.
                    if len(prompt_preview) > 80:
                        prompt_preview = prompt_preview[:80] + "..."

                    print(f"  [{i}] {phone}")
                    print(f"      Voice: {voice}")
                    print(f"      Model: {model}")
                    print(f"      Prompt: {prompt_preview}")

                    # Check for transfer configuration.
                    transfer_list = number_config.get("transfer_list")
                    if transfer_list:
                        departments = list(transfer_list.keys())
                        print(f"      Transfers: {', '.join(departments)}")

                    print()

                # Uncomment the line below to see the full raw JSON response
                # for debugging or detailed inspection.
                # print(json.dumps(numbers, indent=2))
            else:
                # If the response is not a list, print it as-is for debugging.
                print("Response:")
                print(json.dumps(data, indent=2))
        else:
            print(f"Error: Received status code {response.status_code}")
            print(json.dumps(data, indent=2))

        return data

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


if __name__ == "__main__":
    list_numbers()
