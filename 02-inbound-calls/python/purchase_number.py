"""
purchase_number.py
==================
Buy an inbound phone number from Bland AI.

This script sends a POST request to the Bland AI API to purchase a new phone
number. Once purchased, the number costs $15/month and will appear on your
account. You can then configure an AI agent to answer calls on this number
using configure_inbound.py.

Usage:
    1. Copy .env.example to .env and add your API key.
    2. (Optional) Change AREA_CODE or COUNTRY_CODE below.
    3. Run: python purchase_number.py

Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from the .env file in this directory.
# This pulls in BLAND_API_KEY so we do not hardcode secrets in source files.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Your Bland AI API key, loaded from the .env file.
# If you prefer, you can paste it directly here (not recommended for security).
API_KEY = os.getenv("BLAND_API_KEY")

# The Bland AI API base URL for purchasing inbound numbers.
PURCHASE_URL = "https://api.bland.ai/v1/inbound/purchase"

# Three-digit area code for the new number. Change this to any valid US or
# Canadian area code. Common examples:
#   "415" = San Francisco, CA
#   "212" = New York, NY
#   "312" = Chicago, IL
#   "737" = Austin, TX
#   "416" = Toronto, ON (Canada)
AREA_CODE = "415"

# Country code. Bland AI currently supports:
#   "US" = United States
#   "CA" = Canada
COUNTRY_CODE = "US"

# (Optional) If you want a specific phone number, set it here in the format
# "+12223334444". Leave as None to let Bland pick an available number for you.
SPECIFIC_NUMBER = None

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def purchase_number():
    """
    Purchase a new inbound phone number from Bland AI.

    Returns the full API response as a dictionary, which includes the
    purchased phone number on success.
    """

    # Verify the API key is set before making the request.
    if not API_KEY:
        print("Error: BLAND_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return None

    # Build the request headers. Bland AI uses the raw API key in the
    # Authorization header (no "Bearer" prefix).
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }

    # Build the request body with the desired area code and country.
    payload = {
        "area_code": AREA_CODE,
        "country_code": COUNTRY_CODE,
    }

    # If a specific number was requested, include it in the payload.
    # The API will attempt to purchase that exact number if it is available.
    if SPECIFIC_NUMBER:
        payload["phone_number"] = SPECIFIC_NUMBER

    print(f"Purchasing a phone number with area code {AREA_CODE} ({COUNTRY_CODE})...")
    print(f"Request URL: {PURCHASE_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()

    try:
        # Send the POST request to the Bland AI purchase endpoint.
        response = requests.post(PURCHASE_URL, json=payload, headers=headers)

        # Parse the JSON response body.
        data = response.json()

        # Check for a successful response.
        if response.status_code == 200:
            print("Success! Phone number purchased.")
            print(json.dumps(data, indent=2))
            print()
            print("Next step: Copy the phone number from the response above")
            print("and paste it into configure_inbound.py as the INBOUND_NUMBER.")
        else:
            # The API returned an error. Print the status code and body
            # so you can diagnose the issue.
            print(f"Error: Received status code {response.status_code}")
            print(json.dumps(data, indent=2))

        return data

    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, and other request failures.
        print(f"Request failed: {e}")
        return None


if __name__ == "__main__":
    purchase_number()
