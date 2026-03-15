# 08 - Appointment Scheduling with Custom Tools

This cookbook shows you how to build an AI phone agent that checks real-time calendar availability and books appointments during a live call. The agent uses Bland AI's custom tools feature to interact with your calendar API, letting callers browse open slots and confirm bookings without ever speaking to a human.

## What You Will Build

A complete appointment scheduling system with two components:

1. **A calendar server** that exposes availability and booking endpoints (runs locally or on your server)
2. **A Bland AI phone agent** configured with two custom tools (`check_availability` and `book_appointment`) that call your server during the conversation

The finished agent can:

- Ask the caller what service they need and when they are available
- Query your calendar for open time slots on a given date
- Present the available options naturally in conversation
- Book the caller's chosen slot and read back confirmation details
- Handle edge cases like no availability, full days, and rescheduling requests

## Architecture

```
+------------------+          +------------------+          +--------------------+
|                  |  1. Call  |                  |          |                    |
|   Caller (Phone) +--------->+   Bland AI       |          |  Your Calendar     |
|                  |<---------+   Agent          |          |  Server            |
|                  |  Voice   |                  |          |  (Express / Flask) |
+------------------+          |                  |          |                    |
                              |  2. Agent hears  |          |                    |
                              |     "next        |          |                    |
                              |      Tuesday"    |          |                    |
                              |                  |  3. POST |                    |
                              |  Tool:           +--------->+ /api/availability  |
                              |  check_          |<---------+                    |
                              |  availability    |  4. JSON |                    |
                              |                  |  slots   |                    |
                              |  5. Agent reads  |          |                    |
                              |     slots aloud  |          |                    |
                              |                  |          |                    |
                              |  6. Caller picks |          |                    |
                              |     "10 AM"      |          |                    |
                              |                  |  7. POST |                    |
                              |  Tool:           +--------->+ /api/book          |
                              |  book_           |<---------+                    |
                              |  appointment     |  8. JSON |                    |
                              |                  |  confirm |                    |
                              |  9. Agent reads  |          |                    |
                              |     confirmation |          |                    |
                              +------------------+          +--------------------+
```

**Step by step flow:**

1. A caller dials in (or the agent calls them).
2. The AI agent asks what service they want and when they are available.
3. The agent triggers the `check_availability` tool, which sends a POST request to your calendar server.
4. Your server responds with a JSON list of open time slots.
5. The agent reads the available slots to the caller in natural language.
6. The caller picks a slot.
7. The agent triggers the `book_appointment` tool, sending the booking details to your server.
8. Your server creates the appointment and returns a confirmation number.
9. The agent reads the confirmation details back to the caller.

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account.** Sign up at [app.bland.ai](https://app.bland.ai) if you do not have one.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.
- **A phone number to call.** You need a real phone number in E.164 format (e.g., `+15551234567`).
- **ngrok** (or a similar tunneling tool) to expose your local calendar server to the internet so Bland's servers can reach it.

For the **Python** examples:
- Python 3.7 or later
- `requests`, `flask`, and `python-dotenv` packages

For the **Node.js** examples:
- Node.js 18 or later
- `axios`, `express`, and `dotenv` packages

## Quick Start

### Python

```bash
# Terminal 1: Start the calendar server
cd python
pip install flask requests python-dotenv
cp .env.example .env
# Edit .env and add your API key and phone number
python calendar_server.py

# Terminal 2: Expose the server with ngrok
ngrok http 5100

# Terminal 3: Send the scheduling call
# First, update CALENDAR_SERVER_URL in .env with your ngrok URL
python scheduling_agent.py
```

### Node.js

```bash
# Terminal 1: Start the calendar server
cd node
npm install express axios dotenv
cp .env.example .env
# Edit .env and add your API key and phone number
node calendarServer.js

# Terminal 2: Expose the server with ngrok
ngrok http 5100

# Terminal 3: Send the scheduling call
# First, update CALENDAR_SERVER_URL in .env with your ngrok URL
node schedulingAgent.js
```

## Step-by-Step Guide

### Step 1: Start the Calendar Server

The calendar server provides two endpoints that the AI agent calls during the conversation:

- `POST /api/availability` accepts a date and service type, then returns available time slots.
- `POST /api/book` accepts booking details and returns a confirmation number.

Both endpoints use in-memory storage for this demo. In production, you would connect these to a real calendar system (see "Connecting to Real Calendar APIs" below).

Run the server:

```bash
# Python
python calendar_server.py
# Server starts on http://localhost:5100

# Node.js
node calendarServer.js
# Server starts on http://localhost:5100
```

Test it manually with curl:

```bash
# Check availability
curl -X POST http://localhost:5100/api/availability \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-calendar-key" \
  -d '{"date": "2026-03-20", "service": "cleaning"}'

# Book an appointment
curl -X POST http://localhost:5100/api/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-calendar-key" \
  -d '{"date": "2026-03-20", "time": "10:00 AM", "service": "cleaning", "customer_name": "Jane Doe", "customer_phone": "+15551234567"}'
```

### Step 2: Expose Your Server with ngrok

Bland's servers need to reach your calendar server over the internet. During development, use ngrok to create a public URL that tunnels to your local machine:

```bash
ngrok http 5100
```

ngrok will display a forwarding URL like `https://abc123.ngrok-free.app`. Copy this URL. You will use it as the `CALENDAR_SERVER_URL` in your `.env` file.

**Important:** Every time you restart ngrok, you get a new URL. Update your `.env` file accordingly.

### Step 3: Configure and Send the Call

Update your `.env` file with:
- Your Bland API key
- The phone number to call
- Your ngrok URL as the calendar server URL
- An authorization key for your calendar server (any string you choose)

Then run the scheduling agent script:

```bash
# Python
python scheduling_agent.py

# Node.js
node schedulingAgent.js
```

### Step 4: Test the Full Flow

1. Answer the phone when it rings.
2. Tell the agent you want to book a service (e.g., "I need a dental cleaning").
3. When the agent asks about your preferred date, give a date (e.g., "next Friday").
4. The agent will pause briefly while it checks availability, then read you the open slots.
5. Pick a time slot.
6. The agent will book the appointment and read back your confirmation number.

Watch your calendar server's terminal output to see the requests come in as the agent uses each tool.

## Understanding the Tools Schema

Custom tools are the core of this cookbook. They let the AI agent make HTTP requests to your server during the conversation, based on what the caller says. Here is a detailed breakdown of each field.

### Tool 1: check_availability

```json
{
  "name": "check_availability",
  "description": "Check available appointment slots for a given date and service type",
  "url": "https://your-server.com/api/availability",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_CALENDAR_KEY"
  },
  "body": {
    "date": "{{input.date}}",
    "service": "{{input.service}}"
  },
  "input_schema": {
    "example": {
      "date": "2026-03-15",
      "service": "haircut"
    },
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "description": "The date to check in YYYY-MM-DD format"
      },
      "service": {
        "type": "string",
        "description": "The type of service requested"
      }
    }
  },
  "response": {
    "available_slots": "$.available_slots",
    "provider_name": "$.provider_name"
  },
  "speech": "Let me check what times are available for you."
}
```

**Field-by-field explanation:**

| Field | Purpose |
|-------|---------|
| `name` | A unique identifier the AI uses internally to decide which tool to call. Must be lowercase with underscores. |
| `description` | Tells the AI *when* to use this tool. The model reads this description to determine if the tool is relevant to what the caller is asking. Be specific. |
| `url` | The endpoint the tool sends its HTTP request to. This must be publicly accessible (use ngrok for local development). |
| `method` | The HTTP method. Usually `POST` for tools that send data. |
| `headers` | HTTP headers sent with the request. Include authentication and content type here. |
| `body` | The JSON body sent to your server. Values wrapped in `{{input.field_name}}` are filled in dynamically by the AI based on the conversation. |
| `input_schema` | Describes the parameters the AI needs to extract from the conversation. The `example` field helps the model understand the expected format. The `properties` object describes each field's type and purpose. |
| `response` | Maps fields from your server's JSON response to variables the AI can reference. Uses JSONPath syntax (`$.field_name`). The AI will use these values in its next response to the caller. |
| `speech` | What the agent says to the caller *while* the tool request is in flight. This fills the silence during the API call so the conversation feels natural. |

### Tool 2: book_appointment

```json
{
  "name": "book_appointment",
  "description": "Book an appointment for the caller at a specific date, time, and service",
  "url": "https://your-server.com/api/book",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_CALENDAR_KEY"
  },
  "body": {
    "date": "{{input.date}}",
    "time": "{{input.time}}",
    "service": "{{input.service}}",
    "customer_name": "{{input.customer_name}}",
    "customer_phone": "{{input.customer_phone}}"
  },
  "input_schema": {
    "example": {
      "date": "2026-03-15",
      "time": "10:00 AM",
      "service": "haircut",
      "customer_name": "John Smith",
      "customer_phone": "+15551234567"
    },
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "description": "Appointment date in YYYY-MM-DD format"
      },
      "time": {
        "type": "string",
        "description": "Appointment time like '10:00 AM'"
      },
      "service": {
        "type": "string",
        "description": "Service type"
      },
      "customer_name": {
        "type": "string",
        "description": "Customer's full name"
      },
      "customer_phone": {
        "type": "string",
        "description": "Customer's phone number"
      }
    }
  },
  "response": {
    "confirmation_number": "$.confirmation_number",
    "appointment_time": "$.appointment_time",
    "provider_name": "$.provider_name"
  },
  "speech": "Perfect, I am booking that for you right now."
}
```

This tool has five input fields instead of two. The AI extracts all five from the conversation before calling the endpoint. If the caller has not yet provided their name or phone number, the agent will ask for them before triggering this tool.

## How the Agent Decides When to Use Each Tool

The AI does not follow a rigid script. Instead, it reads the `description` field of each tool and decides based on the conversation context:

1. **check_availability** is triggered when the caller mentions a date or asks about openings. The description says "Check available appointment slots for a given date and service type," so the model knows to use it whenever the conversation involves finding open times.

2. **book_appointment** is triggered when the caller confirms a specific slot. The description says "Book an appointment for the caller at a specific date, time, and service," so the model waits until it has all the required information before calling this tool.

The agent will not call `book_appointment` until the caller has explicitly chosen a time slot. Similarly, it will not call `check_availability` until it knows the date and service type. If any required information is missing, the agent asks for it first.

## Verifying It Works

There are several ways to confirm the full flow is working:

### 1. Watch the server logs

Your calendar server prints every request it receives. When the agent calls `check_availability`, you will see the incoming date and service. When it calls `book_appointment`, you will see the full booking details and generated confirmation number.

### 2. Check the call transcript

After the call ends, retrieve the call details from the Bland API:

```bash
curl -X GET https://api.bland.ai/v1/calls/YOUR_CALL_ID \
  -H "Authorization: YOUR_API_KEY"
```

The `concatenated_transcript` field shows the full conversation, including moments where the agent used the tools.

### 3. Check the bookings endpoint

The demo calendar server stores all bookings in memory. Visit `http://localhost:5100/api/bookings` in your browser to see all appointments that have been booked.

### 4. Use the Bland dashboard

Log in to [app.bland.ai](https://app.bland.ai) and navigate to the Calls tab. Click on your call to see the transcript, summary, recording, and tool usage details.

## Testing with ngrok

For local development, ngrok creates a secure tunnel from the public internet to your local machine:

1. Install ngrok from [ngrok.com](https://ngrok.com).
2. Run `ngrok http 5100` to expose your calendar server.
3. Copy the `https://` forwarding URL (e.g., `https://abc123.ngrok-free.app`).
4. Set `CALENDAR_SERVER_URL` in your `.env` file to this URL.
5. Run the scheduling agent script.

**Tips for ngrok:**

- The free tier gives you a new URL every time you restart. Update `.env` each time.
- If you have a paid ngrok plan, you can set a stable subdomain with `ngrok http --subdomain=my-calendar 5100`.
- Check the ngrok web dashboard at `http://localhost:4040` to inspect all requests flowing through the tunnel.

## Connecting to Real Calendar APIs

The demo server uses in-memory storage, but in production you will want to connect to a real calendar system. Here are integration guides for popular platforms.

### Google Calendar

Replace the in-memory logic with Google Calendar API calls:

1. Create a project in the [Google Cloud Console](https://console.cloud.google.com).
2. Enable the Google Calendar API.
3. Create OAuth 2.0 credentials or a service account.
4. Use the `googleapis` npm package (Node.js) or `google-api-python-client` (Python) to query `events.list` for availability and `events.insert` for bookings.

```python
# Python example (pseudocode)
from googleapiclient.discovery import build

service = build("calendar", "v3", credentials=credentials)

# Check availability by listing events in a time range
events = service.events().list(
    calendarId="primary",
    timeMin="2026-03-15T09:00:00Z",
    timeMax="2026-03-15T17:00:00Z",
    singleEvents=True
).execute()

# Find gaps between existing events to determine open slots
```

### Calendly

Use the [Calendly API v2](https://developer.calendly.com):

1. Generate a Personal Access Token in Calendly settings.
2. Use the `/event_types` endpoint to list bookable services.
3. Use the `/availability` endpoint to check open slots.
4. Use the `/scheduled_events` endpoint to create bookings.

### Cal.com

Use the [Cal.com API](https://cal.com/docs/api):

1. Generate an API key in your Cal.com settings.
2. Use `GET /availability` to check open slots for a given date range.
3. Use `POST /bookings` to create a new booking.

Cal.com is open source, so you can also self-host it and connect directly to the database if you prefer.

## Troubleshooting

### The agent says it is checking availability but nothing happens

- Confirm your calendar server is running and listening on port 5100.
- Confirm ngrok is running and the forwarding URL matches what is in your `.env` file.
- Check the ngrok dashboard at `http://localhost:4040` for incoming requests.
- Check for errors in your calendar server's terminal output.

### The agent never triggers the tools

- Make sure the `tools` array is included in your API call payload.
- Verify that the tool `description` fields are clear. The AI uses these to decide when to call each tool.
- Try being more explicit in the conversation: "I want to book an appointment for March 20th."

### The agent triggers the tool but gets an error

- Check that the `url` in the tool definition is correct and publicly accessible.
- Verify the `Authorization` header matches what your server expects.
- Look at the request body in the ngrok dashboard to confirm the data format is correct.

### "Connection refused" errors

- Your calendar server might not be running. Start it with `python calendar_server.py` or `node calendarServer.js`.
- ngrok might have timed out and generated a new URL. Restart ngrok and update `.env`.

### Bookings are lost when the server restarts

This is expected with the demo server, which uses in-memory storage. For persistent bookings, connect to a database or a real calendar API (see "Connecting to Real Calendar APIs" above).

## Next Steps

Now that you have a working appointment scheduling agent, consider these enhancements:

- **Add more services.** Expand the calendar server to support multiple service types with different durations and providers.
- **Connect a real calendar.** Integrate Google Calendar, Calendly, or Cal.com so bookings appear on your actual schedule.
- **Send confirmation SMS.** Use the Bland API's SMS features or a service like Twilio to text the caller their confirmation details.
- **Add cancellation and rescheduling.** Create additional tools like `cancel_appointment` and `reschedule_appointment`.
- **Enable inbound calls.** Set up a Bland inbound number so callers can reach the scheduling agent directly.
- **Add a webhook.** Use the `webhook` parameter to receive call completion data and trigger downstream workflows (e.g., sending a calendar invite email).

Check out the other cookbooks in this series for more patterns, including batch calling campaigns, inbound call handling, and advanced pathway-based agents.
