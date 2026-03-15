# 03 - Conversational Pathways

Build structured, multi-step conversation flows that guide your AI phone agent through branching dialogue trees. Pathways give you fine-grained control over what the agent says, when it transitions between topics, and what information it collects along the way.

## When to Use Pathways vs. Simple Task Prompts

**Use a simple task prompt** when your call has a single goal and the conversation is mostly linear. For example: "Call this person, tell them their appointment is tomorrow at 3pm, and ask them to confirm."

**Use a pathway** when:

- The conversation has multiple distinct stages (greeting, qualification, scheduling, confirmation)
- You need branching logic ("if the caller asks about pricing, go here; if they want support, go there")
- You want to enforce conditions before the agent moves on (e.g., the agent must collect a date, time, and party size before confirming a reservation)
- You need to extract structured data from the conversation and reuse it later
- You want certain responses (like FAQ answers) to be accessible from any point in the conversation

## Core Concepts

### Nodes

Nodes are **conversation states**. Each node represents a phase of the call where the agent has a specific job to do. A node contains:

- **Prompt**: Dynamic instructions telling the agent how to behave in this state. You can reference variables here with `{{variable_name}}`.
- **Text**: A static script the agent will say verbatim when entering this node (optional).
- **Condition**: Requirements that must be satisfied before the agent is allowed to leave this node. For example, "the user must provide their date, time, and party size."
- **Type**: The node's behavior type. Options include `Default`, `End Call`, `Transfer Call`, `Webhook`, `Knowledge Base`, and `Wait for Response`.

### Edges

Edges **connect nodes** and define when the agent should transition from one node to another. Each edge has a **label** that describes the condition or trigger for the transition. The agent reads these labels to decide which path to follow based on the conversation.

For example, an edge labeled "User wants to make a reservation" tells the agent to follow that path when the caller expresses interest in booking.

### Conditions

Conditions act as **gates** on a node. The agent will stay on that node until every condition is met. This is critical for data collection: you can require the agent to gather a name, email, and phone number before it moves forward. Without conditions, the agent might transition too early and miss required information.

### Variables

Variables let you **extract data** from the conversation and **carry it forward** to later nodes. You define variables with the `extractVars` field as an array of `[name, type, description]` tuples.

Once extracted, reference any variable in a prompt or text field using double curly braces:

```
Your reservation is on {{date}} at {{time}} for {{party_size}} guests.
```

#### Built-in Variables

These are available in every pathway without any setup:

| Variable | Description |
|----------|-------------|
| `{{lastUserMessage}}` | The most recent thing the caller said |
| `{{prevNodePrompt}}` | The prompt from the previous node |
| `{{now_utc}}` | Current UTC timestamp |
| `{{from}}` | The phone number the call is coming from |
| `{{to}}` | The phone number the call is going to |
| `{{call_id}}` | Unique identifier for this call |

### Global Nodes

A **global node** is accessible from any other node in the pathway. When the agent enters a global node, it handles the interaction and then returns to whatever node the caller was previously on. This is perfect for FAQ handling, where a caller might ask about business hours at any point in the conversation.

Mark a node as global by setting `isGlobal: true` and providing a `globalLabel` that tells the agent when to jump to this node.

### Global Prompt

The **global prompt** (set via `globalConfig.globalPrompt`) applies context and instructions to every node in the pathway at once. Use it for things like brand voice, general policies, or information the agent should always have available regardless of which node it is on.

## How It Works: Step by Step

### Step 1: Create an Empty Pathway

First, create a pathway with just a name and description. This gives you a `pathway_id` you will use for everything else.

```
POST https://api.bland.ai/v1/pathway
Body: { "name": "Restaurant Reservations", "description": "Handles table bookings for Mario's Italian Kitchen" }
```

### Step 2: Add Nodes and Edges

Update the pathway by sending the full node and edge structure. Each node needs a unique `id`, a `type`, and a `data` object with the node's configuration.

```
POST https://api.bland.ai/v1/pathway/{pathway_id}
Body: { "name": "...", "nodes": [...], "edges": [...], "globalConfig": {...} }
```

### Step 3: Send a Call Using the Pathway

When dispatching a call, pass `pathway_id` instead of `task`. You can also send `request_data` to pre-populate variables before the call starts.

```
POST https://api.bland.ai/v1/calls
Body: { "phone_number": "+1...", "pathway_id": "uuid", "request_data": { "restaurant_name": "Mario's" } }
```

## Example Pathway: Restaurant Reservation

The example code in this cookbook builds a five-node pathway for handling restaurant reservations at "Mario's Italian Kitchen":

```
[Greeting] --(wants reservation)--> [Reservation Details] --(details collected)--> [Confirm Reservation] --(confirmed)--> [End Call]
     |                                                                                    |
     |----(has a question)----> [Handle Questions (global)] <----(has a question)--------|
```

**Nodes:**

1. **Greeting** (start node): Welcomes the caller and routes them to the right place.
2. **Reservation Details**: Collects date, time, and party size. Has a condition that requires all three before moving on. Extracts variables `date`, `time`, and `party_size`.
3. **Confirm Reservation**: Reads back the reservation details using `{{date}}`, `{{time}}`, and `{{party_size}}`. Asks for confirmation.
4. **Handle Questions** (global node): Answers common questions about hours, menu, and location. Accessible from any other node and returns the caller to where they were.
5. **End Call**: Thanks the caller and ends the conversation.

## Best Practices

### Keep nodes focused
Each node should have one clear job. If a node is trying to do too much, split it into two nodes connected by an edge. Focused nodes are easier to debug and produce more predictable agent behavior.

### Write descriptive edge labels
Edge labels are instructions to the agent, not just labels for you. Write them as clear conditions: "The user has provided all reservation details and is ready to confirm" is better than "next."

### Use conditions for required data
Never rely on the agent remembering to collect information. Set explicit conditions: "Do not proceed until the user has provided their date, time, and party size." The agent will stay on the node until conditions are satisfied.

### Extract variables early
Define `extractVars` on the node where data is first mentioned. This ensures the data is available for all downstream nodes. If you wait to extract, you risk losing the information.

### Use global nodes for FAQs
Instead of duplicating FAQ handling across multiple nodes, create a single global node. This keeps your pathway clean and ensures consistent answers no matter where the caller is in the flow.

### Set a global prompt for brand consistency
Use `globalConfig.globalPrompt` for instructions that apply everywhere: tone of voice, company policies, things the agent should never say. This avoids repeating the same context in every node prompt.

### Test with real calls
After building your pathway, make a test call to walk through every branch. Listen for awkward transitions, missing data, and places where the agent gets stuck. Iterate on edge labels and conditions based on what you hear.

## Files in This Cookbook

### Python

| File | What it does |
|------|-------------|
| `create_pathway.py` | Creates a pathway, populates it with the restaurant reservation nodes and edges, then prints the pathway ID |
| `send_call_with_pathway.py` | Dispatches a phone call using an existing pathway ID |
| `list_pathways.py` | Lists all pathways on your account |
| `.env.example` | Template for required environment variables |

### Node.js

| File | What it does |
|------|-------------|
| `createPathway.js` | Creates a pathway, populates it with the restaurant reservation nodes and edges, then prints the pathway ID |
| `sendCallWithPathway.js` | Dispatches a phone call using an existing pathway ID |
| `listPathways.js` | Lists all pathways on your account |
| `.env.example` | Template for required environment variables |

## Setup

### Python

```bash
cd 03-pathways/python
cp .env.example .env
# Edit .env with your API key and phone number
pip install requests python-dotenv
python create_pathway.py
```

### Node.js

```bash
cd 03-pathways/node
cp .env.example .env
# Edit .env with your API key and phone number
npm init -y
npm install axios dotenv
node createPathway.js
```

## Further Reading

- [Pathways API Reference](https://docs.bland.ai)
- [Full API Documentation](https://docs.bland.ai/llms.txt)
- [Bland AI Discord Community](https://discord.gg/QvxDz8zcKe)
