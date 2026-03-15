"""
lead_caller.py
==============
Speed to Lead: Instantly call new leads with Bland AI.

This module provides a single function, call_lead(), that takes lead data
(name, phone, email, source, product interest) and immediately fires off
a Bland AI outbound call to qualify the lead.

The AI agent will:
  - Greet the lead by name
  - Reference what they were interested in
  - Ask qualifying questions (budget, timeline, decision maker)
  - Offer to transfer qualified leads to a live sales rep
  - Leave a personalized voicemail if the lead does not answer

Usage:
    1. Copy .env.example to .env and add your credentials.
    2. Run directly: python lead_caller.py
       (This sends a test call using the example lead data at the bottom.)
    3. Or import and call from your own code:
       from lead_caller import call_lead
       result = call_lead("Jane Smith", "+15551234567", "jane@example.com",
                          "Website Form", "Enterprise Plan")

Dependencies:
    pip install requests python-dotenv
"""

import os
import json
import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load environment variables from the .env file in this directory.
# This pulls in BLAND_API_KEY, WEBHOOK_URL, and TRANSFER_NUMBER so we do
# not hardcode secrets or configuration in source files.
# ---------------------------------------------------------------------------
load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Your Bland AI API key, loaded from the .env file.
# Find yours at https://app.bland.ai under Settings > API Keys.
API_KEY = os.getenv("BLAND_API_KEY")

# The Bland AI endpoint for sending outbound calls.
CALLS_URL = "https://api.bland.ai/v1/calls"

# The public URL where Bland will POST call results when the call finishes.
# This must be publicly accessible. Use ngrok for local testing.
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-server.com/webhook/call-complete")

# Phone number for transferring qualified leads to a live sales rep.
# The AI agent will transfer the call if the lead is highly interested.
TRANSFER_NUMBER = os.getenv("TRANSFER_NUMBER", "+15559876543")

# Additional transfer targets for routing to different departments.
# The AI agent chooses the right one based on conversation context.
SALES_NUMBER = os.getenv("SALES_NUMBER", "+15559876543")
SUPPORT_NUMBER = os.getenv("SUPPORT_NUMBER", "+15551112222")

# Your company name, used in the qualification prompt and voicemail message.
COMPANY_NAME = os.getenv("COMPANY_NAME", "Acme Corp")


def build_qualification_prompt(company_name):
    """
    Build the qualification prompt for the AI agent.

    This prompt instructs the agent on how to handle the lead call. It uses
    dynamic variables (wrapped in double curly braces) that Bland replaces
    at call time with the actual values from request_data.

    Args:
        company_name (str): The name of your company to include in the prompt.

    Returns:
        str: The full prompt string for the AI agent.
    """

    # The prompt follows BANT qualification methodology:
    #   B - Budget: Do they have money to spend?
    #   A - Authority: Are they the decision maker?
    #   N - Need: What problem are they solving?
    #   T - Timeline: When do they want to act?
    #
    # The agent is instructed to ask these questions naturally within a
    # conversational flow, not as a rigid checklist.
    prompt = f"""You are a friendly, professional sales development representative for {company_name}. You are calling {{{{lead_name}}}} who just expressed interest in {{{{product_interest}}}} through {{{{lead_source}}}}.

Your goals on this call:
1. Greet them warmly by name and reference what they were looking at.
2. Confirm they are the right person and that now is a good time to talk.
3. Ask these qualifying questions naturally (do not read them like a list):
   - What problem are they trying to solve?
   - What is their timeline for making a decision?
   - Who else is involved in the decision?
   - Do they have a budget range in mind?
4. Based on their answers, determine if they are a qualified lead.
5. If they seem qualified and interested, offer to transfer them to a specialist right now, or offer to book a demo at a time that works for them.
6. If they are not qualified or not interested, thank them politely and let them know you will send a follow-up email with more information.

Important rules:
- Be conversational and natural. Do not sound like a robot reading a script.
- Do not ask all questions at once. Let the conversation flow naturally.
- If they seem busy, offer to call back at a better time.
- Never be pushy or aggressive. You are here to help, not to hard sell.
- If they ask a question you cannot answer, say you will have a specialist follow up with the answer.
- Keep the call concise. Aim for 3 to 5 minutes unless the lead wants to keep talking.
- Always be polite, even if the lead is not interested.

Their email on file is {{{{lead_email}}}}. You can reference this if needed to confirm identity or offer to send information."""

    return prompt


def build_voicemail_message(company_name):
    """
    Build the voicemail message the agent leaves if the lead does not answer.

    This message is personalized using the same dynamic variables from
    request_data. Bland replaces {{lead_name}} and {{product_interest}}
    with the actual values at call time.

    Args:
        company_name (str): The name of your company for the voicemail.

    Returns:
        str: The voicemail message string.
    """

    # Keep voicemail messages short (under 30 seconds when spoken).
    # Include: who you are, why you are calling, and a call to action.
    message = (
        f"Hi {{{{lead_name}}}}, this is Alex from {company_name}. "
        f"You recently expressed interest in {{{{product_interest}}}} and I wanted "
        f"to connect with you personally. I will send you a follow-up email with "
        f"some helpful information. If you would like to chat, you can call us "
        f"back at this number anytime. Looking forward to connecting with you!"
    )

    return message


def call_lead(name, phone, email, source, interest):
    """
    Trigger an immediate Bland AI call to a new lead.

    This function builds the full API payload with personalized prompt,
    voicemail handling, transfer configuration, and dynamic variables,
    then sends it to the Bland AI /v1/calls endpoint.

    Args:
        name (str): The lead's full name (e.g., "Jane Smith").
        phone (str): The lead's phone number in E.164 format (e.g., "+15551234567").
        email (str): The lead's email address.
        source (str): Where the lead came from (e.g., "Website Contact Form").
        interest (str): What product or service the lead is interested in.

    Returns:
        dict: The API response from Bland AI, containing call_id on success.
        None: If the API key is missing or the request fails.
    """

    # ---------------------------------------------------------------------------
    # Validate that the API key is available before making the request.
    # Without this, the API will return a 401 Unauthorized error.
    # ---------------------------------------------------------------------------
    if not API_KEY:
        print("Error: BLAND_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return None

    # ---------------------------------------------------------------------------
    # Build the request headers.
    # Bland AI uses the raw API key in the Authorization header (no "Bearer" prefix).
    # ---------------------------------------------------------------------------
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
    }

    # ---------------------------------------------------------------------------
    # Build the API payload with all call parameters.
    # ---------------------------------------------------------------------------
    payload = {
        # The lead's phone number. Must be in E.164 format.
        "phone_number": phone,

        # The qualification prompt that defines how the AI agent behaves.
        # This contains dynamic variable placeholders (e.g., {{lead_name}})
        # that Bland replaces with values from request_data at call time.
        "task": build_qualification_prompt(COMPANY_NAME),

        # The very first sentence the agent speaks when the call connects.
        # Personalizing this with the lead's name immediately builds rapport
        # and shows this is not a generic robocall.
        "first_sentence": (
            f"Hi {name}, this is Alex from {COMPANY_NAME}. "
            f"I saw you were just looking at our {interest} options and "
            f"wanted to personally reach out. Do you have a quick moment?"
        ),

        # The voice the agent uses. Choose a professional, friendly voice.
        # Options include: "mason", "maya", "ryan", "tina", "josh",
        # "florian", "derek", "june", "nat", "paige".
        "voice": "mason",

        # The AI model to use. "base" supports all features including
        # transfers, tools, and voicemail detection. "turbo" has lower
        # latency but may not support every feature.
        "model": "base",

        # Maximum call duration in minutes. Qualification calls should be
        # kept short. 10 minutes is plenty for a qualification conversation.
        # The call ends automatically after this duration.
        "max_duration": 10,

        # Enable call recording so you can review conversations later.
        # The recording URL will be included in the post-call webhook data.
        "record": True,

        # Dynamic variables injected into the prompt. Any key here can be
        # referenced in the task prompt using {{key_name}} syntax.
        # These personalize the call without changing the prompt itself.
        "request_data": {
            "lead_name": name,
            "lead_email": email,
            "lead_source": source,
            "product_interest": interest,
        },

        # The URL where Bland sends a POST request with full call data
        # (transcript, summary, variables, recording URL) when the call ends.
        # This must be publicly accessible from the internet.
        "webhook": WEBHOOK_URL,

        # Default phone number for transferring the call. If the AI agent
        # decides the lead is qualified and offers a transfer, the call
        # routes to this number.
        "transfer_phone_number": TRANSFER_NUMBER,

        # Transfer list with multiple department options. The AI agent
        # chooses the appropriate department based on the conversation.
        # For example, if the lead mentions a technical issue, the agent
        # might transfer to "support" instead of "sales".
        "transfer_list": {
            "default": TRANSFER_NUMBER,
            "sales": SALES_NUMBER,
            "support": SUPPORT_NUMBER,
        },

        # Voicemail configuration. If the call goes to voicemail, the agent
        # leaves a personalized message instead of hanging up silently.
        # "action" can be "leave_message", "hangup", or "ignore".
        "voicemail": {
            "action": "leave_message",
            "message": build_voicemail_message(COMPANY_NAME),
        },

        # Custom tools the agent can use during the call. This example
        # includes a booking tool that lets the agent schedule a demo.
        # The tool definition tells the AI what the tool does, what
        # parameters it needs, and where to send the request.
        "tools": [
            {
                # A descriptive name for the tool. The AI uses this to
                # understand when to invoke it.
                "name": "BookDemo",

                # A clear description so the AI knows when to use this tool.
                # Be specific about the trigger conditions.
                "description": (
                    "Use this tool when the lead wants to schedule a demo "
                    "or a follow-up meeting. Collect their preferred date "
                    "and time before calling this tool."
                ),

                # The URL that receives the tool invocation. Replace this
                # with your actual scheduling API endpoint.
                "url": "https://your-server.com/api/book-demo",

                # The HTTP method for the tool request.
                "method": "POST",

                # The headers sent with the tool request. You can include
                # authentication headers for your scheduling API here.
                "headers": {
                    "Content-Type": "application/json",
                },

                # Input schema defining what parameters the AI should collect
                # from the lead before invoking the tool.
                "input_schema": {
                    "type": "object",
                    "properties": {
                        # The lead's name, pre-filled from call context.
                        "name": {
                            "type": "string",
                            "description": "The lead's full name.",
                        },
                        # The lead's email for sending calendar invites.
                        "email": {
                            "type": "string",
                            "description": "The lead's email address.",
                        },
                        # The preferred date and time for the demo.
                        "preferred_datetime": {
                            "type": "string",
                            "description": (
                                "The lead's preferred date and time for the "
                                "demo, in natural language (e.g., 'next "
                                "Tuesday at 2 PM')."
                            ),
                        },
                    },
                    # All fields are required before the tool can be invoked.
                    "required": ["name", "email", "preferred_datetime"],
                },

                # The speech the agent says while waiting for the tool
                # response. This fills the silence so the lead does not
                # think the call dropped.
                "speech": (
                    "Let me check our availability for that time. "
                    "One moment please."
                ),
            }
        ],
    }

    # ---------------------------------------------------------------------------
    # Log the outgoing request for debugging purposes.
    # In production, you would use a proper logging framework.
    # ---------------------------------------------------------------------------
    print(f"Calling lead: {name} at {phone}")
    print(f"Source: {source}")
    print(f"Interest: {interest}")
    print(f"Webhook URL: {WEBHOOK_URL}")
    print()

    try:
        # Send the POST request to the Bland AI calls endpoint.
        # The API responds immediately with a call_id. The actual phone call
        # is placed asynchronously by Bland's infrastructure.
        response = requests.post(CALLS_URL, json=payload, headers=headers)

        # Parse the JSON response body.
        data = response.json()

        # Check for a successful response (HTTP 200).
        if response.status_code == 200:
            call_id = data.get("call_id", "unknown")
            print(f"Call successfully queued!")
            print(f"Call ID: {call_id}")
            print(f"Status: {data.get('status', 'unknown')}")
            print()
            print("The lead's phone will ring within seconds.")
            print("Post-call results will be sent to your webhook URL.")
        else:
            # The API returned an error. Print details for debugging.
            print(f"Error: Received status code {response.status_code}")
            print(json.dumps(data, indent=2))

        return data

    except requests.exceptions.RequestException as e:
        # Handle network errors, timeouts, DNS failures, etc.
        print(f"Request failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Main: Run this file directly to send a test call.
# Replace the example values below with real data for testing.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Example lead data for testing.
    # Replace these with your own values. Use your personal phone number
    # so you can answer the call and test the conversation.
    test_lead = {
        "name": "Jane Smith",
        "phone": "+15551234567",       # Replace with your real phone number
        "email": "jane@example.com",
        "source": "Website Contact Form",
        "interest": "Enterprise Plan",
    }

    print("=" * 60)
    print("Speed to Lead: Sending test call")
    print("=" * 60)
    print()

    result = call_lead(
        name=test_lead["name"],
        phone=test_lead["phone"],
        email=test_lead["email"],
        source=test_lead["source"],
        interest=test_lead["interest"],
    )

    if result:
        print()
        print("Full API response:")
        print(json.dumps(result, indent=2))
