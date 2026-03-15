"""
create_agent.py

Creates a Bland AI Web Agent that can be used for browser-based voice conversations.
The agent is a persistent configuration, meaning you create it once and then authorize
individual sessions against it. Think of it like a template for conversations.

Usage:
    1. Copy .env.example to .env and fill in your Bland API key.
    2. Run: python create_agent.py
    3. Copy the agent_id from the output and save it in your .env file as BLAND_AGENT_ID.

Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 1. Load environment variables from the .env file in the same directory.
#    This keeps sensitive values like your API key out of source control.
# ---------------------------------------------------------------------------
load_dotenv()

# Read the API key from the environment. This key authenticates all requests
# to the Bland API. You can find it in your Bland dashboard under Settings > API Keys.
BLAND_API_KEY = os.getenv("BLAND_API_KEY")

# Validate that the API key is present before making any requests.
if not BLAND_API_KEY:
    raise ValueError(
        "BLAND_API_KEY is not set. "
        "Copy .env.example to .env and add your API key."
    )

# ---------------------------------------------------------------------------
# 2. Define the Bland API endpoint for creating agents.
# ---------------------------------------------------------------------------
CREATE_AGENT_URL = "https://api.bland.ai/v1/agents"

# ---------------------------------------------------------------------------
# 3. Set up request headers.
#    - Authorization: Your raw API key (no "Bearer" prefix needed).
#    - Content-Type: Must be application/json for the request body.
# ---------------------------------------------------------------------------
headers = {
    "Authorization": BLAND_API_KEY,
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# 4. Build the agent configuration payload.
#    This defines everything about how the agent behaves during conversations.
# ---------------------------------------------------------------------------
agent_config = {
    # prompt (string, required):
    # The core instructions for your agent. This tells the AI who it is,
    # how it should behave, what it knows, and what it should do.
    # Write this as if you are briefing a new employee on their role.
    "prompt": (
        "You are a friendly and knowledgeable customer support assistant for Acme Corp, "
        "a software company that makes project management tools. Your name is Alex.\n\n"
        "Your responsibilities:\n"
        "- Answer questions about Acme Corp's products and pricing\n"
        "- Help users troubleshoot common issues\n"
        "- Collect feedback and feature requests\n"
        "- Escalate complex technical issues by recommending the user email support@acme.com\n\n"
        "Guidelines:\n"
        "- Be conversational and warm, but stay professional\n"
        "- Keep responses concise (1 to 3 sentences when possible)\n"
        "- If you do not know the answer, say so honestly\n"
        "- Never make up information about products or pricing\n\n"
        "Pricing information:\n"
        "- Free tier: Up to 5 users, basic features\n"
        "- Pro tier: $12/user/month, advanced features and integrations\n"
        "- Enterprise tier: Custom pricing, dedicated support and SLAs\n\n"
        "If the user provides their name, greet them by name. "
        "You can access the user's name via the variable {{name}} if it was provided."
    ),

    # voice (string, optional, default "mason"):
    # Which voice the agent uses to speak. Each voice has a distinct tone
    # and personality. Try different voices to find the best fit for your brand.
    # Options include: "mason", "maya", "ryan", "tina", "josh", "florian",
    # "derek", "june", "nat", "paige"
    "voice": "mason",

    # first_sentence (string, optional, max 200 characters):
    # The exact sentence the agent says at the start of every conversation.
    # If omitted, the agent generates its own greeting based on the prompt.
    # Keep it short and welcoming.
    "first_sentence": "Hi there! Welcome to Acme Corp support. How can I help you today?",

    # language (string, optional, default "ENG"):
    # The language for the conversation. The agent will both listen and
    # respond in this language. Default is English.
    "language": "ENG",

    # model (string, optional, default "base"):
    # Which AI model powers the agent.
    # - "base": Full feature support, reliable for most use cases
    # - "turbo": Lower latency (faster responses), but may lack some features
    # For most web agent use cases, "base" is recommended.
    "model": "base",

    # interruption_threshold (number, optional, default 500):
    # Controls how patient the agent is before it starts responding,
    # measured in milliseconds. Lower values make the agent jump in faster
    # when there is a pause. Higher values let the user finish longer thoughts.
    # Recommended range: 50 to 200 for responsive web agents.
    "interruption_threshold": 100,

    # max_duration (number, optional, default 30):
    # Maximum conversation length in minutes. The session automatically
    # ends after this duration. Set this based on your expected conversation
    # length to prevent runaway sessions.
    "max_duration": 15,

    # keywords (string[], optional):
    # Words or phrases that the transcription engine should prioritize.
    # Use this for product names, technical terms, or brand-specific
    # vocabulary that might otherwise be misheard.
    "keywords": ["Acme Corp", "Pro tier", "Enterprise"],

    # metadata (object, optional):
    # Custom key-value pairs attached to the agent for your own tracking.
    # These are returned in webhooks and call details, making it easy to
    # filter and organize conversations in your system.
    "metadata": {
        "department": "customer_support",
        "version": "1.0",
    },

    # analysis_schema (object, optional):
    # Defines structured data that Bland extracts from each conversation
    # after it ends. This is useful for automatically capturing insights
    # without needing to parse the transcript yourself.
    "analysis_schema": {
        "topic": "string: The main topic the user asked about (e.g., pricing, troubleshooting, feedback)",
        "sentiment": "string: The overall sentiment of the user (positive, neutral, or negative)",
        "resolved": "boolean: Whether the user's question was fully answered",
        "follow_up_needed": "boolean: Whether the user needs additional follow-up",
    },
}

# ---------------------------------------------------------------------------
# 5. Send the request to create the agent.
# ---------------------------------------------------------------------------
print("Creating web agent...")
print(f"Endpoint: {CREATE_AGENT_URL}")
print()

response = requests.post(CREATE_AGENT_URL, headers=headers, json=agent_config)

# ---------------------------------------------------------------------------
# 6. Handle the response.
#    A successful response returns a status of "success" along with the
#    full agent object, including the agent_id you need for authorizing sessions.
# ---------------------------------------------------------------------------
if response.status_code == 200:
    data = response.json()

    if data.get("status") == "success":
        agent = data.get("agent", {})
        agent_id = agent.get("agent_id")

        print("Agent created successfully!")
        print(f"Agent ID: {agent_id}")
        print(f"Voice: {agent.get('voice')}")
        print(f"Model: {agent.get('model')}")
        print()
        print("Next steps:")
        print(f"  1. Add this to your .env file: BLAND_AGENT_ID={agent_id}")
        print("  2. Run authorize_session.py to get a session token")
        print("  3. Use the token with BlandWebClient in the browser")
    else:
        print("Unexpected response format:")
        print(json.dumps(data, indent=2))
else:
    # Print the error details for debugging.
    print(f"Error: HTTP {response.status_code}")
    print(response.text)
