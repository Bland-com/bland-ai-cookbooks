"""
create_pathway.py

Creates a restaurant reservation pathway for Mario's Italian Kitchen,
then populates it with nodes, edges, conditions, and variable extraction.

This script demonstrates the full pathway lifecycle:
  1. Create an empty pathway (gets you a pathway_id)
  2. Define nodes (conversation states)
  3. Define edges (transitions between nodes)
  4. Update the pathway with the complete structure

Usage:
  1. Copy .env.example to .env and fill in your API key
  2. pip install requests python-dotenv
  3. python create_pathway.py
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

# Your Bland AI API key. Grab it from https://app.bland.ai under Developer settings.
BLAND_API_KEY = os.getenv("BLAND_API_KEY")

# Base URL for all Bland AI API requests
BASE_URL = "https://api.bland.ai/v1"

# Every request to Bland needs your API key in the Authorization header.
# Note: Bland does not use "Bearer" prefix, just the raw key.
HEADERS = {
    "Authorization": BLAND_API_KEY,
    "Content-Type": "application/json",
}


def create_empty_pathway():
    """
    Step 1: Create an empty pathway.

    This gives us a pathway_id that we can then populate with nodes and edges.
    Think of it as creating a blank canvas before you start drawing.

    POST https://api.bland.ai/v1/pathway
    Body: { "name": "...", "description": "..." }
    Returns: { "status": "success", "pathway_id": "uuid" }
    """
    url = f"{BASE_URL}/pathway"

    payload = {
        # A human-readable name for this pathway. Shows up in the Bland dashboard.
        "name": "Mario's Italian Kitchen Reservations",

        # A short description of what this pathway does.
        # Helps you identify it later when you have many pathways.
        "description": (
            "Handles restaurant reservations for Mario's Italian Kitchen. "
            "Collects date, time, and party size, then confirms the booking. "
            "Also answers common questions about hours, menu, and location."
        ),
    }

    print("Creating empty pathway...")
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()  # Raise an exception for HTTP errors

    data = response.json()
    pathway_id = data.get("pathway_id")
    print(f"Pathway created successfully. ID: {pathway_id}")

    return pathway_id


def build_nodes():
    """
    Step 2: Define the nodes (conversation states).

    Each node represents a distinct phase of the conversation. The agent
    follows the prompt at each node and uses edge labels to decide when
    to move to the next node.

    Node fields:
      - id: A unique string identifier (e.g., "1", "2", "3")
      - type: The behavior type. Options:
          "Default"             Standard conversation node
          "End Call"            Hangs up the call
          "Transfer Call"       Transfers to a human agent
          "Webhook"             Fires an HTTP request mid-call
          "Knowledge Base"      Queries a knowledge base
          "Wait for Response"   Pauses and waits for the user to speak
      - data: An object containing the node's configuration:
          - name:          Display name (shown in the Bland dashboard)
          - isStart:       true for the entry point node (exactly one per pathway)
          - isGlobal:      true if this node should be accessible from any other node
          - globalLabel:   When isGlobal is true, this label tells the agent when
                           to jump to this node (e.g., "User asks a general question")
          - prompt:        Dynamic instructions for the agent. Supports {{variables}}.
          - text:          Static text the agent says verbatim when entering this node.
                           Use this for greetings or scripted lines.
          - condition:     Requirements that must be met before the agent can leave.
                           The agent stays on this node until all conditions are satisfied.
          - extractVars:   An array of [varName, varType, varDescription] tuples.
                           The agent extracts these from the conversation automatically.
          - modelOptions:  Fine-tune the AI model for this specific node:
                           modelName, interruptionThreshold, temperature
    """
    nodes = [
        # ---------------------------------------------------------------
        # Node 1: Greeting (Start Node)
        # This is where every call begins. The agent welcomes the caller
        # and figures out what they need.
        # ---------------------------------------------------------------
        {
            "id": "1",
            "type": "Default",
            "data": {
                "name": "Greeting",
                # Mark this as the entry point. Only one node can be the start.
                "isStart": True,
                "isGlobal": False,
                # Static text the agent will say when the call connects.
                # Using "text" instead of "prompt" here ensures the agent
                # says this exact line before doing anything else.
                "text": (
                    "Welcome to Mario's Italian Kitchen! "
                    "How can I help you today?"
                ),
                # The prompt gives the agent context for how to behave.
                # After saying the greeting text, it follows these instructions.
                "prompt": (
                    "You are a friendly receptionist at Mario's Italian Kitchen. "
                    "Greet the caller warmly. Find out if they want to make a "
                    "reservation, ask a question about the restaurant, or something else. "
                    "Be conversational and welcoming."
                ),
            },
        },
        # ---------------------------------------------------------------
        # Node 2: Reservation Details
        # This is where the agent collects the three required pieces of
        # information: date, time, and party size. The condition prevents
        # the agent from moving on until all three are gathered.
        # ---------------------------------------------------------------
        {
            "id": "2",
            "type": "Default",
            "data": {
                "name": "Reservation Details",
                "isStart": False,
                "isGlobal": False,
                "prompt": (
                    "You are collecting reservation details. You need three pieces "
                    "of information from the caller:\n"
                    "1. The date they want to dine\n"
                    "2. The time they want to arrive\n"
                    "3. The number of guests (party size)\n\n"
                    "Ask for each one naturally. If the caller provides multiple "
                    "details at once, acknowledge all of them. Be conversational, "
                    "not robotic. For example, say 'Great, and how many people will "
                    "be joining you?' rather than 'Please provide party size.'"
                ),
                # The condition is critical here. It acts as a gate that keeps
                # the agent on this node until all three details are collected.
                # Without this, the agent might move to confirmation too early.
                "condition": (
                    "The user must provide all three of the following: "
                    "the date of the reservation, the time of the reservation, "
                    "and the number of guests (party size). Do not proceed until "
                    "all three are clearly stated by the user."
                ),
                # extractVars tells the agent to pull structured data from the
                # conversation. Each entry is [name, type, description].
                # Once extracted, these variables are available in later nodes
                # as {{date}}, {{time}}, and {{party_size}}.
                "extractVars": [
                    # [variable_name, variable_type, description_for_the_agent]
                    ["date", "string", "The date of the reservation (e.g., 'March 15th', 'next Friday')"],
                    ["time", "string", "The time of the reservation (e.g., '7pm', '6:30 in the evening')"],
                    ["party_size", "string", "The number of guests (e.g., '4', 'two people', 'a party of six')"],
                ],
            },
        },
        # ---------------------------------------------------------------
        # Node 3: Confirm Reservation
        # Reads back the collected details and asks the caller to confirm.
        # Notice how {{date}}, {{time}}, and {{party_size}} are used in
        # the prompt. These were extracted in the previous node.
        # ---------------------------------------------------------------
        {
            "id": "3",
            "type": "Default",
            "data": {
                "name": "Confirm Reservation",
                "isStart": False,
                "isGlobal": False,
                "prompt": (
                    "Read back the reservation details to the caller and ask them "
                    "to confirm. Say something like: 'Just to confirm, I have a "
                    "reservation for {{party_size}} guests on {{date}} at {{time}}. "
                    "Does that sound right?'\n\n"
                    "If the caller wants to change something, help them adjust the "
                    "details. If they confirm, let them know the reservation is set."
                ),
                # A lighter condition here: just need a yes or no from the caller.
                "condition": (
                    "The user must either confirm the reservation details are correct "
                    "or request a change. Do not proceed until the user responds."
                ),
            },
        },
        # ---------------------------------------------------------------
        # Node 4: Handle Questions (Global Node)
        # This is a GLOBAL node, meaning it is accessible from any other
        # node in the pathway. If the caller asks a question about hours,
        # menu, or location at any point, the agent jumps here, answers
        # the question, and then returns to wherever the caller was.
        # ---------------------------------------------------------------
        {
            "id": "4",
            "type": "Default",
            "data": {
                "name": "Handle Questions",
                "isStart": False,
                # Setting isGlobal to true makes this node reachable from everywhere.
                "isGlobal": True,
                # The globalLabel tells the agent when to jump to this node.
                # It acts like a trigger condition visible from all other nodes.
                "globalLabel": "The caller asks a general question about the restaurant (hours, menu, location, parking, etc.)",
                "prompt": (
                    "Answer the caller's question about Mario's Italian Kitchen. "
                    "Here is the restaurant information:\n\n"
                    "Hours: Tuesday to Sunday, 11:30 AM to 10:00 PM. Closed on Mondays.\n"
                    "Location: 742 Evergreen Terrace, Springfield.\n"
                    "Parking: Free parking lot behind the building. Street parking also available.\n"
                    "Menu highlights: Handmade pasta, wood-fired pizza, tiramisu. "
                    "Full bar with Italian wine selection.\n"
                    "Dietary options: Vegetarian, vegan, and gluten-free options available. "
                    "Let your server know about any allergies.\n\n"
                    "After answering, ask if there is anything else you can help with."
                ),
            },
        },
        # ---------------------------------------------------------------
        # Node 5: End Call
        # The final node. Thanks the caller and hangs up.
        # Using type "End Call" tells the system to terminate the call
        # after the agent delivers the closing message.
        # ---------------------------------------------------------------
        {
            "id": "5",
            "type": "End Call",
            "data": {
                "name": "End Call",
                "isStart": False,
                "isGlobal": False,
                "prompt": (
                    "Thank the caller for calling Mario's Italian Kitchen. "
                    "If they made a reservation, remind them of the details: "
                    "'We look forward to seeing your party of {{party_size}} on "
                    "{{date}} at {{time}}.' If they just had a question, say "
                    "'Thanks for calling, have a great day!' End the conversation warmly."
                ),
            },
        },
    ]

    return nodes


def build_edges():
    """
    Step 3: Define the edges (transitions between nodes).

    Edges connect nodes and tell the agent when to move from one node to
    another. Each edge has:
      - id:     A unique string identifier for the edge
      - source: The id of the node the edge comes from
      - target: The id of the node the edge goes to
      - label:  A description of when the agent should follow this edge.
                The agent reads these labels to decide which path to take
                based on the conversation.

    Tips for writing edge labels:
      - Be specific and descriptive. "User wants to make a reservation" is
        better than "next" or "continue".
      - Write from the agent's perspective. The label answers the question
        "When should I follow this edge?"
      - If two edges leave the same node, make the labels mutually exclusive
        so the agent knows which one to pick.
    """
    edges = [
        # From Greeting to Reservation Details:
        # The caller wants to book a table.
        {
            "id": "edge_1_2",
            "source": "1",      # Greeting
            "target": "2",      # Reservation Details
            "label": "The caller wants to make a reservation or book a table",
        },
        # From Greeting to End Call:
        # The caller is done after the greeting (maybe they just had a quick question
        # handled by the global node, or they realized they called the wrong place).
        {
            "id": "edge_1_5",
            "source": "1",      # Greeting
            "target": "5",      # End Call
            "label": "The caller has no further questions and wants to end the call",
        },
        # From Reservation Details to Confirm Reservation:
        # The agent has successfully collected date, time, and party size.
        # This edge only activates after the node's condition is met.
        {
            "id": "edge_2_3",
            "source": "2",      # Reservation Details
            "target": "3",      # Confirm Reservation
            "label": "The caller has provided the date, time, and party size for the reservation",
        },
        # From Confirm Reservation to End Call:
        # The caller confirmed the reservation, and we are wrapping up.
        {
            "id": "edge_3_5",
            "source": "3",      # Confirm Reservation
            "target": "5",      # End Call
            "label": "The caller has confirmed the reservation details are correct",
        },
        # From Confirm Reservation back to Reservation Details:
        # The caller wants to change something (wrong date, different time, etc.)
        {
            "id": "edge_3_2",
            "source": "3",      # Confirm Reservation
            "target": "2",      # Reservation Details
            "label": "The caller wants to change the reservation details (date, time, or party size)",
        },
    ]

    # Note: We do NOT need edges to/from the global "Handle Questions" node (id "4").
    # Global nodes are automatically reachable from every other node based on
    # their globalLabel. The agent jumps to the global node when the label
    # condition is met, then returns to the previous node afterward.

    return edges


def build_global_config():
    """
    Build the global configuration.

    The globalPrompt is injected into every node in the pathway. Use it for
    instructions that should apply universally: brand voice, policies, things
    the agent should always or never say.

    This keeps your individual node prompts focused on their specific task
    while the global prompt handles cross-cutting concerns.
    """
    return {
        "globalPrompt": (
            "You are a friendly and professional receptionist at Mario's Italian Kitchen, "
            "an upscale Italian restaurant. Always be warm, polite, and helpful. "
            "Use a conversational tone, not a robotic one. "
            "If you don't know the answer to something, say 'Let me check on that for you' "
            "rather than making something up. "
            "Never discuss competitors or other restaurants. "
            "The restaurant's phone number is (555) 867-5309."
        ),
    }


def update_pathway_with_structure(pathway_id, nodes, edges, global_config):
    """
    Step 4: Update the pathway with the full node/edge structure.

    This sends the complete pathway definition to the API. You can call
    this endpoint multiple times to update or modify the pathway.

    POST https://api.bland.ai/v1/pathway/{pathway_id}
    Body: { "name": "...", "nodes": [...], "edges": [...], "globalConfig": {...} }
    """
    url = f"{BASE_URL}/pathway/{pathway_id}"

    payload = {
        "name": "Mario's Italian Kitchen Reservations",
        "description": (
            "Handles restaurant reservations for Mario's Italian Kitchen. "
            "Collects date, time, and party size, then confirms the booking."
        ),
        "nodes": nodes,
        "edges": edges,
        "globalConfig": global_config,
    }

    print(f"\nUpdating pathway {pathway_id} with {len(nodes)} nodes and {len(edges)} edges...")
    response = requests.post(url, json=payload, headers=HEADERS)
    response.raise_for_status()

    data = response.json()
    print("Pathway updated successfully!")
    print(f"\nFull response:\n{json.dumps(data, indent=2)}")

    return data


def main():
    """
    Main function: creates a pathway, builds the node/edge structure,
    and pushes it to the Bland AI API.
    """
    # Validate that the API key is set
    if not BLAND_API_KEY:
        print("Error: BLAND_API_KEY is not set.")
        print("Copy .env.example to .env and add your API key.")
        return

    # Step 1: Create the empty pathway
    pathway_id = create_empty_pathway()

    # Step 2: Build the node and edge definitions
    nodes = build_nodes()
    edges = build_edges()
    global_config = build_global_config()

    # Step 3: Update the pathway with the full structure
    update_pathway_with_structure(pathway_id, nodes, edges, global_config)

    # Print a summary of what we built
    print("\n" + "=" * 60)
    print("PATHWAY SUMMARY")
    print("=" * 60)
    print(f"Pathway ID:    {pathway_id}")
    print(f"Nodes:         {len(nodes)}")
    print(f"Edges:         {len(edges)}")
    print(f"Global nodes:  {sum(1 for n in nodes if n['data'].get('isGlobal'))}")
    print(f"Variables:     date, time, party_size")
    print(f"\nUse this pathway_id to send calls:")
    print(f"  python send_call_with_pathway.py")
    print(f"\nOr add it to your .env file:")
    print(f"  PATHWAY_ID={pathway_id}")


if __name__ == "__main__":
    main()
