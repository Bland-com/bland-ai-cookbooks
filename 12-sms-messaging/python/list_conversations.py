"""
Bland AI - List SMS Conversations (Python)

This script retrieves all SMS conversations from your Bland AI account
and displays them in a readable format with conversation IDs, phone numbers,
message counts, and statuses.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python list_conversations.py

The script will:
    - Fetch all SMS conversations from the API
    - Display each conversation's key details in a formatted table
    - Show the total number of conversations

Note: SMS messaging is an Enterprise feature. Your account must have
SMS enabled to use this endpoint.
"""

import os
import sys

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load environment variables from the .env file in this directory.
load_dotenv()

# Your Bland API key. Found in the Bland dashboard under Settings > API Keys.
API_KEY = os.getenv("BLAND_API_KEY")

# The Bland API base URL. All SMS endpoints are under /v1/sms.
BASE_URL = "https://api.bland.ai/v1"

# ---------------------------------------------------------------------------
# Validate configuration
# ---------------------------------------------------------------------------

# Only the API key is needed for listing conversations. No phone numbers
# are required since we are just reading data.

if not API_KEY:
    print("Error: BLAND_API_KEY is not set.")
    print("Copy .env.example to .env and add your API key.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Fetch SMS conversations
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
}

print("Fetching SMS conversations...")
print()

try:
    # Make the GET request to the List Conversations endpoint.
    # This returns all SMS conversations associated with your account.
    response = requests.get(
        "{}/sms/conversations".format(BASE_URL),
        headers=headers,
        timeout=30,  # 30-second timeout for the HTTP request itself
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

    if response.status_code == 401:
        print()
        print("This usually means your API key is invalid or missing.")
    elif response.status_code == 403:
        print()
        print("SMS may not be enabled on your plan.")
        print("SMS is an Enterprise feature. Contact Bland support to enable it.")

    sys.exit(1)

# ---------------------------------------------------------------------------
# Display the conversations
# ---------------------------------------------------------------------------

# Parse the JSON response. The response may be a list of conversations
# directly, or an object with a "conversations" key depending on the
# API version. We handle both cases.
data = response.json()

# Extract the conversations list from the response.
# The API may return the list directly or nested under a key.
if isinstance(data, list):
    # The response is a list of conversations directly.
    conversations = data
elif isinstance(data, dict):
    # The response is an object. Look for a "conversations" key,
    # or fall back to treating the whole response as a single-item list.
    conversations = data.get("conversations", data.get("data", []))
    if not isinstance(conversations, list):
        conversations = [data]
else:
    print("Unexpected response format:")
    print(data)
    sys.exit(1)

# Check if there are any conversations to display.
if not conversations:
    print("No SMS conversations found.")
    print()
    print("To create your first conversation, run:")
    print("  python create_conversation.py")
    print()
    print("Or send a message with:")
    print("  python send_sms.py")
    sys.exit(0)

# Print a header for the conversation list.
print("Found {} conversation(s):".format(len(conversations)))
print()
print("{:<40} {:<16} {:<16} {:<10} {:<12}".format(
    "Conversation ID", "From", "To", "Messages", "Status"
))
print("-" * 94)

# Iterate through each conversation and display its details.
# We use .get() with default values to handle missing fields gracefully,
# since the API response may not include all fields for every conversation.
for convo in conversations:
    # The unique identifier for this conversation. Use this to fetch
    # full conversation details or analyze the conversation.
    convo_id = convo.get("id", convo.get("conversation_id", "N/A"))

    # The Bland phone number that sent the messages.
    from_number = convo.get("from", convo.get("from_number", "N/A"))

    # The recipient's phone number.
    to_number = convo.get("to", convo.get("phone_number", "N/A"))

    # The total number of messages exchanged in this conversation.
    # This includes both sent and received messages.
    messages = convo.get("message_count", convo.get("messages", "N/A"))
    if isinstance(messages, list):
        # If "messages" is the actual message array, count its length.
        messages = len(messages)

    # The current status of the conversation (e.g., "active", "completed").
    status = convo.get("status", "N/A")

    # Print the conversation row in the formatted table.
    print("{:<40} {:<16} {:<16} {:<10} {:<12}".format(
        str(convo_id)[:38],
        str(from_number)[:14],
        str(to_number)[:14],
        str(messages),
        str(status)[:10],
    ))

# Print a summary footer.
print()
print("Total conversations: {}".format(len(conversations)))
print()
print("To view full details for a specific conversation,")
print("use the conversation ID with the Get Conversation endpoint:")
print("  GET https://api.bland.ai/v1/sms/conversations/<conversation_id>")
print()
print("To analyze a conversation, use the Analyze endpoint:")
print("  POST https://api.bland.ai/v1/sms/analyze")
print("  Body: {{ \"conversation_id\": \"<id>\", \"goal\": \"...\", \"questions\": [...] }}")
