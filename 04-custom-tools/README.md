# 04 - Custom Tools

Custom tools let your AI phone agent call external APIs in the middle of a live conversation. Instead of just talking, the agent can look up customer records, book appointments, check inventory, process payments, and more, all while the caller waits naturally on the line.

This cookbook walks you through the full lifecycle: defining a tool schema, attaching it to a call, and building the webhook server that handles tool requests.

## What You Will Build

1. **An Appointment Booking tool** that extracts a date, time, and service from the conversation, sends a request to your booking endpoint, and reads back a confirmation number.
2. **A CRM Lookup tool** that takes a phone number or email, looks up the customer in your system, and gives the agent their account details so it can personalize the rest of the call.
3. **A webhook server** (Flask for Python, Express for Node.js) that receives tool requests from Bland, processes them, and returns structured responses.

## How Custom Tools Work

Here is the flow from start to finish:

1. You define a **tool schema** that describes what the tool does, what data to extract, and where to send it.
2. You attach the tool to a call via the `tools` array in the Send Call API.
3. During the call, the agent decides when to use the tool based on the conversation and the tool's `description` field.
4. The agent extracts the required fields from the conversation using the `input_schema`.
5. Bland sends an HTTP request to your `url` with the extracted data in the request body.
6. While waiting for your server to respond, the agent speaks the `speech` text to keep the caller engaged.
7. Your server processes the request and returns a JSON response.
8. Bland maps the response fields to variables using the `response` configuration.
9. The agent uses those variables to continue the conversation with the relevant information.

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account.** Sign up at [app.bland.ai](https://app.bland.ai) if you do not have one.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.
- **A phone number to call.** Use your own number for testing, in E.164 format (e.g., `+15551234567`).
- **A publicly accessible server** (or a tunneling tool like [ngrok](https://ngrok.com)) so Bland can reach your webhook endpoint.

For the **Python** examples:
- Python 3.7 or later
- `requests`, `python-dotenv`, and `flask` packages

For the **Node.js** examples:
- Node.js 18 or later
- `axios`, `dotenv`, and `express` packages

## Quick Start

### Python

```bash
cd python
pip install requests python-dotenv flask
cp .env.example .env
# Edit .env with your API key, phone number, and webhook URL

# Terminal 1: Start the webhook server
python webhook_server.py

# Terminal 2: Create a tool and send a call
python create_tool.py
python send_call_with_tool.py
```

### Node.js

```bash
cd node
npm install axios dotenv express cors
cp .env.example .env
# Edit .env with your API key, phone number, and webhook URL

# Terminal 1: Start the webhook server
node webhookServer.js

# Terminal 2: Create a tool and send a call
node createTool.js
node sendCallWithTool.js
```

## The Tool Schema in Detail

Every custom tool is defined by a JSON object with the following fields:

```json
{
  "name": "book_appointment",
  "description": "Books an appointment for the caller. Use this when the caller wants to schedule a service.",
  "url": "https://your-server.com/api/book",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-internal-api-key"
  },
  "body": {
    "requested_date": "{{input.date}}",
    "requested_time": "{{input.time}}",
    "service_type": "{{input.service}}"
  },
  "input_schema": {
    "example": {
      "speech": "I'd like to book a haircut for tomorrow at 3 PM.",
      "date": "2025-01-15",
      "time": "15:00",
      "service": "haircut"
    },
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "description": "The appointment date in YYYY-MM-DD format."
      },
      "time": {
        "type": "string",
        "description": "The appointment time in HH:MM 24-hour format."
      },
      "service": {
        "type": "string",
        "description": "The type of service being booked."
      }
    }
  },
  "response": {
    "confirmation_number": "$.data.confirmation_id",
    "appointment_time": "$.data.scheduled_time"
  },
  "speech": "Let me book that appointment for you. One moment please."
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | A unique identifier for the tool. Use snake_case with no spaces. |
| `description` | string | Yes | A plain-language explanation of what the tool does. The agent reads this to decide when to invoke the tool, so be specific and clear. |
| `url` | string | Yes | The full URL of your API endpoint that Bland will call. |
| `method` | string | Yes | The HTTP method: `POST`, `GET`, `PUT`, `PATCH`, or `DELETE`. |
| `headers` | object | No | Any HTTP headers to include in the request. Useful for authentication tokens, content types, etc. |
| `body` | object | No | The JSON body to send. Use `{{input.property}}` placeholders to inject extracted values. |
| `input_schema` | object | Yes | Defines the data the agent should extract from the conversation. See below. |
| `response` | object | No | Maps fields from your API response to named variables using JSONPath syntax. |
| `speech` | string | No | What the agent says while waiting for your API to respond. Keeps the conversation natural. |

### How `input_schema` Works

The `input_schema` tells the agent exactly what information to pull from the conversation before calling your API. It follows JSON Schema conventions:

- **`type`**: Always `"object"` for the top level.
- **`properties`**: Each key is a field name. The value includes the field's `type` (string, number, boolean, etc.) and a `description` the agent uses to understand what to extract.
- **`example`**: A sample object showing what a valid extraction looks like. This includes a `speech` field showing an example of what the caller might say, plus the expected extracted values. The example is critical because it teaches the agent the format you expect.

The agent uses the descriptions and the example together to figure out the correct values. For instance, if the caller says "next Tuesday at 2," the agent will convert that to a proper date and time format based on your example.

### How Response Mapping Works

The `response` object maps your API's JSON response to named variables using JSONPath expressions:

```json
"response": {
  "confirmation_number": "$.data.confirmation_id",
  "appointment_time": "$.data.scheduled_time"
}
```

If your API returns:

```json
{
  "data": {
    "confirmation_id": "APT-98712",
    "scheduled_time": "2025-01-15 at 3:00 PM"
  }
}
```

Then after the tool call:
- `{{confirmation_number}}` resolves to `"APT-98712"`
- `{{appointment_time}}` resolves to `"2025-01-15 at 3:00 PM"`

The agent can reference these variables naturally in conversation: "Your appointment is confirmed. Your confirmation number is APT-98712."

### The `speech` Parameter

Without `speech`, there would be dead silence while your API processes the request. The `speech` string fills that gap. Keep it natural and relevant:

- Good: `"Let me check our availability for that date. One moment."`
- Good: `"I'm pulling up your account now."`
- Avoid: `"Processing..."` (too robotic)

## How the Agent Decides When to Use a Tool

The agent reads the `description` field and uses it as a decision rule. When the conversation reaches a point where the tool is relevant, the agent triggers it automatically. You do not need to write explicit branching logic.

Write your descriptions as clear instructions:

- Good: `"Look up a customer's account information by their phone number or email address. Use this when the caller asks about their account, order status, or billing."`
- Weak: `"Customer lookup"` (too vague for the agent to know when to trigger)

The more specific the description, the more reliably the agent will use the tool at the right moment.

## Two Ways to Use Tools

### Option 1: Inline Tools (passed directly in the Send Call request)

Define the tools array directly in your call payload. Best for quick prototyping or one-off calls.

```json
{
  "phone_number": "+15551234567",
  "task": "You are a scheduling assistant...",
  "tools": [ { ...tool_schema... } ]
}
```

### Option 2: Saved Tools (created via the Tools API, referenced by ID)

Create reusable tools via `POST /v1/tools`, then reference them by `tool_id` in your calls. Best for production use when multiple agents share the same tools.

```json
{
  "phone_number": "+15551234567",
  "task": "You are a scheduling assistant...",
  "tools": ["your-tool-id-here"]
}
```

This cookbook demonstrates both approaches.

## Step-by-Step Guide

### Step 1: Start Your Webhook Server

Your webhook server is the API that Bland calls when the agent triggers a tool. Start it locally and expose it with ngrok (or deploy it to a public server).

**Python:**

```bash
cd python
python webhook_server.py
# Server starts on port 5000
```

**Node.js:**

```bash
cd node
node webhookServer.js
# Server starts on port 3001
```

Then in a separate terminal, expose it publicly:

```bash
ngrok http 5000   # for Python (Flask)
ngrok http 3001   # for Node.js (Express)
```

Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`). You will use this as your tool's `url` base.

### Step 2: Create a Saved Tool (Optional)

Run the create tool script to register a reusable appointment booking tool via the Tools API:

```bash
python create_tool.py     # Python
node createTool.js        # Node.js
```

This returns a `tool_id` you can attach to any future call.

### Step 3: Send a Call with Tools Attached

Run the send call script. It defines both the appointment booking and CRM lookup tools inline, then sends a call:

```bash
python send_call_with_tool.py   # Python
node sendCallWithTool.js        # Node.js
```

Answer the phone and try saying something like:
- "I'd like to book a haircut for tomorrow at 2 PM."
- "Can you look up my account? My email is john@example.com."

### Step 4: Watch Your Webhook Server Logs

As the agent triggers tools during the call, you will see incoming requests in your webhook server terminal:

```
[BOOK] Received booking request:
  Date: 2025-01-15
  Time: 14:00
  Service: haircut
[BOOK] Returning confirmation: APT-38291
```

This confirms that the full loop is working: the agent extracted the right data, Bland sent it to your server, and your response was mapped back to variables the agent could use.

## API Reference

### Send Call with Tools

**Endpoint:** `POST https://api.bland.ai/v1/calls`

**Headers:**

| Header | Value | Description |
|--------|-------|-------------|
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |
| `Content-Type` | `application/json` | Required for JSON body |

The `tools` parameter is an array of tool objects (inline) or tool ID strings (saved). All other parameters are the same as the standard Send Call API.

### Create Tool

**Endpoint:** `POST https://api.bland.ai/v1/tools`

**Headers:**

| Header | Value | Description |
|--------|-------|-------------|
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |
| `Content-Type` | `application/json` | Required for JSON body |

**Body:** A single tool schema object (same structure as inline tools).

**Response:**

```json
{
  "tool_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "name": "book_appointment",
  "status": "success"
}
```

### Template Variable Syntax

| Syntax | Context | Description |
|--------|---------|-------------|
| `{{input.property}}` | Tool `body` | References a value extracted from the conversation via `input_schema` |
| `{{variable_name}}` | Agent prompt / conversation | References a value mapped from a tool's API response via `response` |

## Common Issues

### "My tool never gets triggered"

- Check your tool's `description`. If it is too vague, the agent will not know when to use it. Be explicit about the trigger conditions.
- Make sure the `input_schema` properties have clear, descriptive `description` fields. The agent uses these to understand what to extract.
- Verify that your prompt (the `task` field) does not conflict with the tool. For example, do not tell the agent "never ask for personal information" if your tool requires an email address.

### "Bland cannot reach my webhook"

- If running locally, make sure you are using ngrok or a similar tunnel. Bland cannot call `localhost` or `127.0.0.1`.
- Confirm your ngrok tunnel is active and the URL matches the `url` in your tool.
- Check that your server is running on the correct port.

### "The extracted values are wrong or empty"

- Improve the `example` in your `input_schema`. The example teaches the agent the expected format. If your example shows a date as `"2025-01-15"` but the agent sends `"January 15th"`, add more guidance in the property's `description`.
- Make sure each property's `description` is specific. Instead of `"The date"`, use `"The appointment date in YYYY-MM-DD format"`.

### "The agent does not read back the response data"

- Verify your `response` mapping uses correct JSONPath expressions. `$.data.id` means the `id` field inside a `data` object at the root of your response.
- Confirm your webhook server is returning valid JSON with the expected structure.
- Make sure your `task` prompt instructs the agent to confirm details after a booking or lookup. For example: "After booking, read back the confirmation number to the caller."

### "The call works but the agent sounds awkward during tool calls"

- Add or improve the `speech` parameter. Without it, there is silence while Bland waits for your API.
- Keep speech short and natural. One to two sentences is ideal.

### "I get a 400 or 401 from the Bland API"

- Double-check your API key in the `.env` file. No extra spaces, no quotes around the value.
- Make sure the `Authorization` header sends the raw key (not `Bearer sk-...`, just `sk-...`).
- Verify your JSON is valid. A trailing comma or missing bracket will cause a 400.

## Verifying It Works

Here is a checklist to confirm everything is functioning:

1. Your webhook server is running and accessible from the internet (test by visiting the ngrok URL in your browser).
2. The `create_tool.py` / `createTool.js` script returns a `tool_id` without errors.
3. The `send_call_with_tool.py` / `sendCallWithTool.js` script returns a `call_id`.
4. Your phone rings and the agent greets you.
5. When you request a booking or account lookup, the agent says the `speech` text ("One moment...").
6. Your webhook server logs show the incoming request with the correct extracted data.
7. The agent reads back the confirmation number or account details from your server's response.

## Next Steps

- **Add error handling to your tools.** Return error messages from your webhook and instruct the agent (via the prompt) on how to handle failures gracefully.
- **Chain multiple tools.** An agent can use several tools in one call. For example, look up the customer first, then book an appointment under their account.
- **Move to saved tools.** Once your tools are stable, create them via the Tools API so you can reuse them across many calls without duplicating the schema.
- **Add authentication to your webhook.** Use the `headers` field to send a secret token, and validate it on your server to prevent unauthorized requests.
- **Explore Conversational Pathways.** Combine tools with pathway-based flows for complex, multi-step conversations. See cookbook 03 for details.
