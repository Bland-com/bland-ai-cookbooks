"""
create_widget.py

Creates a Bland AI web chat widget via the API. The widget can be embedded on
any website to give visitors an AI-powered chat assistant.

Usage:
    1. Copy .env.example to .env and add your Bland API key.
    2. Run: python create_widget.py
    3. Copy the widget_id from the output and use it in your HTML page.

Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from the .env file in the same directory.
# This keeps your API key out of source control.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Read the API key from the environment. This key authenticates every request
# to the Bland API. You can find yours at https://app.bland.ai under
# Settings > API Keys.
# ---------------------------------------------------------------------------
BLAND_API_KEY = os.getenv("BLAND_API_KEY")

# Validate that the API key is present before making any requests.
if not BLAND_API_KEY:
    raise ValueError(
        "BLAND_API_KEY is not set. "
        "Copy .env.example to .env and add your API key."
    )

# ---------------------------------------------------------------------------
# Bland API endpoint for creating a web chat widget.
# ---------------------------------------------------------------------------
CREATE_WIDGET_URL = "https://api.bland.ai/v1/widget"

# ---------------------------------------------------------------------------
# Request headers. Bland uses the raw API key in the Authorization header
# (no "Bearer" prefix).
# ---------------------------------------------------------------------------
headers = {
    "Authorization": BLAND_API_KEY,
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# Widget configuration payload.
#
# This defines how the chat agent behaves when visitors interact with it.
# You can customize every field below to match your use case.
# ---------------------------------------------------------------------------
widget_config = {
    # -----------------------------------------------------------------------
    # prompt (string, required)
    #
    # The system prompt that defines the agent's personality, knowledge, and
    # behavior. This is the most important field. Write it as if you are
    # training a new support agent: tell it who it is, what it knows, how
    # it should respond, and what it should avoid.
    #
    # You can include dynamic variables using {{variable_name}} syntax.
    # These variables are filled in at runtime from the request_data object
    # passed in window.blandSettings on your HTML page.
    # -----------------------------------------------------------------------
    "prompt": (
        "You are a friendly and knowledgeable customer support agent for "
        "NovaCRM, a modern CRM platform for growing businesses.\n\n"
        "Your name is Nova. You help visitors understand NovaCRM's features, "
        "pricing, and integrations. You can answer questions about:\n"
        "- Plans and pricing (Starter at $19/mo, Pro at $49/mo, Enterprise "
        "at $99/mo)\n"
        "- Key features (contact management, pipeline tracking, email "
        "automation, reporting, API access)\n"
        "- Integrations (Slack, Gmail, Salesforce import, Zapier, webhooks)\n"
        "- Getting started and onboarding\n\n"
        "If the visitor asks something you cannot answer, offer to connect "
        "them with a human team member.\n\n"
        "If the visitor provides their name via request_data, greet them by "
        "name. For example: 'Hi {{first_name}}, welcome to NovaCRM!'\n\n"
        "Keep responses concise, helpful, and friendly. Use short paragraphs."
    ),

    # -----------------------------------------------------------------------
    # voice (string, optional)
    #
    # The voice the agent uses if voice mode is enabled on the widget. This
    # uses the same voice options available for phone calls.
    # Common options: "mason", "maya", "ryan", "tina", "josh", "florian",
    # "derek", "june", "nat", "paige".
    # -----------------------------------------------------------------------
    "voice": "maya",

    # -----------------------------------------------------------------------
    # first_sentence (string, optional)
    #
    # The greeting message the agent sends as soon as a visitor opens the
    # chat. If omitted, the agent generates its own greeting based on the
    # prompt.
    # -----------------------------------------------------------------------
    "first_sentence": (
        "Hey there! I'm Nova, your NovaCRM assistant. "
        "How can I help you today?"
    ),

    # -----------------------------------------------------------------------
    # model (string, optional)
    #
    # Which AI model powers the agent.
    # - "base": Full feature support, recommended for most use cases.
    # - "turbo": Lower latency but may not support all features.
    # -----------------------------------------------------------------------
    "model": "base",

    # -----------------------------------------------------------------------
    # temperature (float, optional)
    #
    # Controls the randomness of the agent's responses.
    # - 0.0: Deterministic, always picks the most likely response.
    # - 1.0: Maximum creativity and variation.
    # - 0.7: A good balance for conversational agents.
    # -----------------------------------------------------------------------
    "temperature": 0.7,

    # -----------------------------------------------------------------------
    # tools (array, optional)
    #
    # Custom tools the agent can invoke during the conversation. Each tool
    # is an API call the agent can trigger when it determines the visitor
    # needs information that requires a live lookup.
    #
    # Below is an example tool that checks pricing for a given plan. In a
    # real application, this would call your own backend API.
    # -----------------------------------------------------------------------
    "tools": [
        {
            # A human-readable name for the tool.
            "name": "check_plan_details",

            # A description that helps the AI decide when to use this tool.
            "description": (
                "Retrieves detailed information about a specific NovaCRM "
                "pricing plan, including features, limits, and current "
                "promotions."
            ),

            # The URL to call when the tool is triggered.
            "url": "https://your-api.example.com/plans/details",

            # The HTTP method to use.
            "method": "GET",

            # The parameters the agent should collect before calling the tool.
            "parameters": {
                "type": "object",
                "properties": {
                    "plan_name": {
                        "type": "string",
                        "description": (
                            "The name of the plan to look up "
                            "(starter, pro, or enterprise)."
                        ),
                    }
                },
                "required": ["plan_name"],
            },
        }
    ],
}

# ---------------------------------------------------------------------------
# Make the API request to create the widget.
# ---------------------------------------------------------------------------
print("Creating Bland AI web chat widget...")
print()

try:
    response = requests.post(
        CREATE_WIDGET_URL,
        headers=headers,
        json=widget_config,
    )

    # Raise an exception for HTTP error status codes (4xx, 5xx).
    response.raise_for_status()

    # Parse the JSON response body.
    data = response.json()

    # -----------------------------------------------------------------------
    # Print the results. The most important field is widget_id, which you
    # will use to embed the widget on your website.
    # -----------------------------------------------------------------------
    print("Widget created successfully!")
    print()
    print(f"  Widget ID: {data.get('widget_id', 'N/A')}")
    print()
    print("Full API response:")
    print(json.dumps(data, indent=2))
    print()
    print("Next steps:")
    print("  1. Copy the widget_id above.")
    print("  2. Open index.html (in the parent directory).")
    print("  3. Replace YOUR_WIDGET_ID with your actual widget ID.")
    print("  4. Open index.html in a browser to see the widget in action.")

except requests.exceptions.HTTPError as http_err:
    # -----------------------------------------------------------------------
    # Handle HTTP errors (bad status codes from the API).
    # Common causes:
    #   401: Invalid API key.
    #   400: Malformed request body.
    #   429: Rate limit exceeded.
    # -----------------------------------------------------------------------
    print(f"HTTP error: {http_err}")
    print(f"Status code: {response.status_code}")
    print(f"Response body: {response.text}")

except requests.exceptions.ConnectionError:
    # -----------------------------------------------------------------------
    # Handle network connectivity issues.
    # -----------------------------------------------------------------------
    print("Connection error: could not reach the Bland API.")
    print("Check your internet connection and try again.")

except requests.exceptions.Timeout:
    # -----------------------------------------------------------------------
    # Handle request timeouts.
    # -----------------------------------------------------------------------
    print("Request timed out. The Bland API may be temporarily unavailable.")
    print("Wait a moment and try again.")

except requests.exceptions.RequestException as err:
    # -----------------------------------------------------------------------
    # Catch-all for any other request-related errors.
    # -----------------------------------------------------------------------
    print(f"An unexpected error occurred: {err}")
