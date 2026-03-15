"""
authorize_session.py

Authorizes a session for a Bland AI Web Agent, returning a single-use token
that the browser can use to start a voice conversation.

Each token can only be used once. After a conversation starts with a given token,
that token is invalidated. Call this endpoint every time a user wants to start
a new conversation.

Usage:
    1. Make sure .env contains both BLAND_API_KEY and BLAND_AGENT_ID.
    2. Run: python authorize_session.py
    3. The script prints the session token that the frontend can use.

Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# 1. Load environment variables from the .env file.
# ---------------------------------------------------------------------------
load_dotenv()

# Your Bland API key. Used to authenticate the authorization request.
# This key must stay on the server and never be sent to the browser.
BLAND_API_KEY = os.getenv("BLAND_API_KEY")

# The agent ID returned when you created the web agent (see create_agent.py).
# This identifies which agent configuration to use for the session.
BLAND_AGENT_ID = os.getenv("BLAND_AGENT_ID")

# Validate that both required environment variables are present.
if not BLAND_API_KEY:
    raise ValueError(
        "BLAND_API_KEY is not set. "
        "Copy .env.example to .env and add your API key."
    )

if not BLAND_AGENT_ID:
    raise ValueError(
        "BLAND_AGENT_ID is not set. "
        "Run create_agent.py first to create an agent, then add the "
        "agent_id to your .env file."
    )

# ---------------------------------------------------------------------------
# 2. Build the authorization endpoint URL.
#    The agent_id is part of the URL path.
# ---------------------------------------------------------------------------
AUTHORIZE_URL = f"https://api.bland.ai/v1/agents/{BLAND_AGENT_ID}/authorize"

# ---------------------------------------------------------------------------
# 3. Set up request headers.
#    - Authorization: Your raw API key (no "Bearer" prefix).
#    - Content-Type: Must be application/json.
# ---------------------------------------------------------------------------
headers = {
    "Authorization": BLAND_API_KEY,
    "Content-Type": "application/json",
}

# ---------------------------------------------------------------------------
# 4. Build the request body.
#    The request_data field lets you pass dynamic variables into the
#    conversation. These values replace {{variable_name}} placeholders
#    in the agent's prompt.
#
#    For example, if your agent prompt says "Hello {{name}}", and you pass
#    { "name": "Sarah" } here, the agent will say "Hello Sarah".
#
#    This is how you personalize each session with user-specific data
#    without modifying the agent's base prompt.
# ---------------------------------------------------------------------------
request_body = {
    # request_data (object, optional):
    # Key-value pairs that get injected into the agent prompt as template
    # variables. Each key becomes available as {{key}} in the prompt.
    # Common uses:
    #   - User's name for personalized greetings
    #   - Account type for tailored responses
    #   - Order IDs or reference numbers for context
    "request_data": {
        "name": "Sarah",
    },
}

# ---------------------------------------------------------------------------
# 5. Send the authorization request.
# ---------------------------------------------------------------------------
print("Authorizing session...")
print(f"Agent ID: {BLAND_AGENT_ID}")
print(f"Endpoint: {AUTHORIZE_URL}")
print()

response = requests.post(AUTHORIZE_URL, headers=headers, json=request_body)

# ---------------------------------------------------------------------------
# 6. Handle the response.
#    A successful response contains a single-use "token" that the browser
#    uses to initialize the BlandWebClient connection.
# ---------------------------------------------------------------------------
if response.status_code == 200:
    data = response.json()

    if data.get("status") == "success":
        token = data.get("token")

        print("Session authorized successfully!")
        print(f"Session Token: {token}")
        print()
        print("This token is single-use. It can only start one conversation.")
        print("Pass this token to BlandWebClient in the browser to begin.")
        print()
        print("Example (JavaScript):")
        print(f'  const client = new BlandWebClient("{BLAND_AGENT_ID}", "{token}");')
        print('  await client.initConversation({ sampleRate: 44100 });')
    else:
        print("Unexpected response format:")
        print(json.dumps(data, indent=2))
else:
    # Print the error details for debugging.
    print(f"Error: HTTP {response.status_code}")
    print(response.text)
