"""
Bland AI - Create a Persona (Python)

This script creates a professional customer service persona using the
Bland AI Personas API. The persona bundles voice, prompt, behavior settings,
and more into a single reusable configuration.

The example persona is "Sarah, Customer Success Manager at TechCorp," a
friendly and knowledgeable agent who helps customers with product questions,
account issues, and technical support.

Usage:
    1. Copy .env.example to .env and fill in your API key.
    2. Install dependencies: pip install requests python-dotenv
    3. Run: python create_persona.py

The script will:
    - Create a new persona via the Bland API
    - Print the persona_id for use in future calls
    - Display the full persona configuration
"""

import json
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
# Define the persona prompt
# ---------------------------------------------------------------------------

# The prompt is the core of your persona. It defines who the agent is, how
# they should behave, what they know, and what their goals are. Write this
# as if you were onboarding a new team member.
#
# Best practices for persona prompts:
#   - Start with a clear identity statement (name, role, company).
#   - Define the agent's primary objective on each call.
#   - List specific behaviors and conversational guidelines.
#   - Include knowledge the agent should reference (products, policies).
#   - Set boundaries for what the agent should not do.
#   - Keep the tone instructions specific ("warm and professional" is better
#     than "be nice").

PERSONA_PROMPT = """You are Sarah, a Customer Success Manager at TechCorp, a leading provider of
cloud-based project management software.

Your primary goal is to ensure every customer feels heard, supported, and confident
in using TechCorp's products. You handle incoming calls about product questions,
account issues, billing inquiries, and basic technical support.

Personality and tone:
- You are warm, patient, and genuinely enthusiastic about helping customers.
- You speak in a professional but approachable manner. Avoid jargon unless the
  customer uses it first.
- You are empathetic. If a customer is frustrated, acknowledge their feelings
  before jumping into solutions.
- You are proactive. If you solve one issue, ask if there is anything else you
  can help with.

Product knowledge:
- TechCorp offers three plans: Starter ($29/month, up to 5 users), Professional
  ($79/month, up to 25 users), and Enterprise (custom pricing, unlimited users).
- All plans include project boards, task management, file sharing, and basic
  reporting. Professional adds advanced analytics, time tracking, and integrations.
  Enterprise adds SSO, audit logs, dedicated support, and custom workflows.
- The platform supports integrations with Slack, Google Workspace, Microsoft 365,
  Jira, and Salesforce.
- A 14-day free trial is available for all plans. No credit card required.

Common tasks you handle:
1. Answering questions about features and pricing.
2. Helping customers upgrade or downgrade their plan.
3. Walking customers through basic setup and configuration.
4. Troubleshooting login issues and password resets.
5. Collecting feedback and feature requests.
6. Scheduling follow-up calls with the technical team for advanced issues.

Guidelines:
- Always verify the customer's identity by asking for their name and email
  address associated with their TechCorp account.
- If you cannot resolve an issue, offer to escalate it to the technical team
  and provide an expected response time (usually within 24 hours).
- Never share internal company information, pricing negotiations, or data
  about other customers.
- Keep your responses concise. One to two sentences at a time works best
  for phone conversations. Avoid long monologues.
- If the customer asks about a competitor, remain neutral and focus on
  TechCorp's strengths without criticizing the competitor.

Closing the call:
- Summarize what was discussed and any action items.
- Confirm the customer's email for any follow-up communication.
- Thank them for being a TechCorp customer.
- Ask if there is anything else you can help with before ending the call.
"""

# ---------------------------------------------------------------------------
# Build the persona configuration
# ---------------------------------------------------------------------------

# This dictionary contains all the parameters for the persona.
# The "name" and "prompt" are the minimum required fields. Everything else
# refines the agent's behavior and is optional.

persona_config = {
    # REQUIRED: A display name for the persona. This helps you identify it
    # in the dashboard and API responses. Use a descriptive name that
    # includes the role and company.
    "name": "Sarah, Customer Success Manager at TechCorp",

    # REQUIRED: The global prompt that defines the agent's personality,
    # knowledge, and behavioral rules. This is the most important field.
    # See the PERSONA_PROMPT variable above for the full content.
    "prompt": PERSONA_PROMPT,

    # OPTIONAL: The voice the agent uses on calls. This should match a
    # voice name from the voice catalog. Run list_voices.py to see all
    # available options.
    # "maya" is a popular female voice with a warm, professional tone
    # that works well for customer service personas.
    "voice": "maya",

    # OPTIONAL: The language for conversations. Default is "babel-en"
    # (English). Change this if your persona handles calls in a
    # different language.
    "language": "babel-en",

    # OPTIONAL: The exact sentence the agent says when the call connects.
    # Setting this ensures a consistent, professional greeting every time.
    # If omitted, the agent generates its own greeting from the prompt.
    "first_sentence": (
        "Hi, thank you for calling TechCorp! This is Sarah from Customer "
        "Success. How can I help you today?"
    ),

    # OPTIONAL: Controls how sensitive the agent is to being interrupted
    # by the caller. This is measured in milliseconds.
    #
    # Lower values (e.g., 50 to 100) mean the agent pauses quickly when
    # the caller starts speaking. This creates a more natural,
    # conversational feel but may cause the agent to stop mid-sentence
    # if there is background noise.
    #
    # Higher values (e.g., 150 to 250) mean the agent is harder to
    # interrupt and will finish more of its response before yielding.
    # This is useful for scripted messages or when the agent needs to
    # deliver important information without being cut off.
    #
    # A value of 100 is a good starting point for customer service,
    # balancing responsiveness with message completion.
    "interruption_threshold": 100,

    # OPTIONAL: Whether the agent waits for the caller to speak first.
    # Set to False for outbound calls where Sarah should greet the caller
    # immediately. Set to True for inbound calls where the caller
    # typically speaks first (e.g., "Hi, I need help with...").
    "wait_for_greeting": False,

    # OPTIONAL: Which AI model to use for generating responses.
    # "base" provides the full feature set including all tools and
    # integrations. "turbo" offers the lowest latency but may not
    # support some advanced features.
    # Use "base" for customer service where quality matters more than
    # raw speed.
    "model": "base",

    # OPTIONAL: Ambient background audio played during the call. This
    # adds a layer of realism that makes the conversation feel more
    # natural, as if the agent is in a real office environment.
    # Options: "office", "cafe", "restaurant", "none", or null.
    # "office" is ideal for a professional customer service persona.
    "background_track": "office",

    # OPTIONAL: A URL that receives a POST request with the full call
    # data when each call using this persona completes. Useful for
    # logging, CRM updates, or triggering downstream workflows.
    # Uncomment and set this to your webhook endpoint.
    # "webhook": "https://your-server.com/api/call-completed",

    # OPTIONAL: IDs of knowledge bases the agent can search during calls.
    # Connect a knowledge base containing your product documentation,
    # FAQ, or help articles so the agent can provide accurate answers.
    # Uncomment and add your knowledge base IDs.
    # "knowledge_base_ids": ["kb-xxxxx-xxxxx"],

    # OPTIONAL: A pathway ID for structured conversation flows. If your
    # persona should follow a specific conversation script or decision
    # tree, connect it to a pathway here.
    # "pathway_id": "pathway-xxxxx-xxxxx",

    # OPTIONAL: Post-call analysis schema. Define fields that the AI
    # should extract and analyze from each call. This is useful for
    # tracking call outcomes, sentiment, and key topics.
    "analysis_schema": {
        # Each key is a field name, and the value describes what to extract.
        # The AI analyzes the transcript after the call and populates these
        # fields automatically.
        "customer_sentiment": "Rate the customer's overall sentiment: positive, neutral, or negative.",
        "issue_category": "Categorize the main issue: billing, technical, feature_question, account, or other.",
        "resolution_status": "Was the issue resolved on the call? Values: resolved, escalated, or follow_up_needed.",
        "plan_discussed": "Which TechCorp plan was discussed, if any? Values: starter, professional, enterprise, or none.",
        "follow_up_required": "Is a follow-up action needed? true or false.",
        "call_summary": "Provide a brief one to two sentence summary of the call.",
    },
}

# ---------------------------------------------------------------------------
# Create the persona via the API
# ---------------------------------------------------------------------------

# Set the authorization header. Bland uses a simple API key in the
# Authorization header (no "Bearer" prefix needed).
headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json",
}

print("Creating persona: {}".format(persona_config["name"]))
print()

try:
    # Make the POST request to the Create Persona endpoint.
    # This creates a new persona on your account and returns the
    # persona_id you will use in future calls.
    response = requests.post(
        "{}/personas".format(BASE_URL),
        json=persona_config,
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

# Parse the JSON response.
data = response.json()

# ---------------------------------------------------------------------------
# Display the results
# ---------------------------------------------------------------------------

# Extract the persona_id from the response. This is the unique identifier
# you will pass as "persona_id" when sending calls.
persona_id = data.get("persona_id") or data.get("id", "Unknown")

print("Persona created successfully!")
print()
print("  Persona ID:  {}".format(persona_id))
print("  Name:        {}".format(persona_config["name"]))
print("  Voice:       {}".format(persona_config["voice"]))
print("  Model:       {}".format(persona_config["model"]))
print("  Language:    {}".format(persona_config["language"]))
print("  Background:  {}".format(persona_config["background_track"]))
print("  Interruption Threshold: {}".format(persona_config["interruption_threshold"]))
print()

# ---------------------------------------------------------------------------
# Next steps
# ---------------------------------------------------------------------------

print("Next steps:")
print()
print("  1. Copy the Persona ID above.")
print("  2. Add it to your .env file as PERSONA_ID={}".format(persona_id))
print("  3. Run send_call_with_persona.py to test the persona with a live call.")
print()
print("You can also view and manage this persona in the Bland dashboard.")
print()

# ---------------------------------------------------------------------------
# Display the full API response for reference
# ---------------------------------------------------------------------------

print("Full API response:")
print("-" * 60)
print(json.dumps(data, indent=2))
print("-" * 60)
