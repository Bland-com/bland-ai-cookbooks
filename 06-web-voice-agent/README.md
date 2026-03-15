# 06 - Web Voice Agent

This cookbook shows you how to add a voice-powered AI assistant to your web application using the Bland AI Web Agent API and the `BlandWebClient` SDK. By the end, you will have a working browser-based voice agent that users can talk to in real time, with no phone call required.

## What You Will Build

A complete voice agent experience consisting of:

1. **A backend script** that creates a web agent via the Bland API with custom prompt, voice, and behavior settings
2. **A session authorization endpoint** that generates single-use tokens for secure client-side connections
3. **An Express server** (Node.js) that serves the frontend and handles session token requests
4. **A frontend page** with a "Start Conversation" button, a live microphone animation, and an "End Conversation" button

The architecture keeps your API key safe on the server while letting the browser connect directly to the Bland voice service using short-lived session tokens.

## Architecture Overview

```
+-------------------+       +-------------------+       +-------------------+
|                   |       |                   |       |                   |
|   Browser         | <---> |   Your Server     | <---> |   Bland API       |
|   (index.html)    |       |   (server.js)     |       |                   |
|                   |       |                   |       |                   |
+-------------------+       +-------------------+       +-------------------+

1. Your server creates a Web Agent (one-time setup)
2. User clicks "Start Conversation" in the browser
3. Browser requests a session token from your server
4. Your server calls Bland's /authorize endpoint with your API key
5. Server returns the session token to the browser
6. Browser uses BlandWebClient with the token to start a voice session
7. User speaks directly to the AI agent through the browser
```

**Why session tokens?** Your API key never leaves your server. Each session token is single-use, meaning it can only start one conversation. If a token is intercepted, it cannot be reused. This prevents unauthorized usage of your Bland account.

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account.** Sign up at [app.bland.ai](https://app.bland.ai) if you do not have one.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.
- **An existing Web Agent ID** (or you will create one using the scripts in this cookbook).

For the **Python** examples:
- Python 3.7 or later
- `requests` and `python-dotenv` packages

For the **Node.js** examples:
- Node.js 18 or later
- `axios`, `dotenv`, `express`, and `cors` packages

For the **frontend**:
- A modern browser (Chrome, Firefox, Safari, or Edge) with microphone access
- The `bland-voice` npm package (loaded via CDN in the example)

## Quick Start

### Step 1: Create an Agent

#### Python

```bash
cd python
pip install requests python-dotenv
cp .env.example .env
# Edit .env and add your API key
python create_agent.py
# Copy the agent_id from the output
```

#### Node.js

```bash
cd node
npm install axios dotenv express cors
cp .env.example .env
# Edit .env and add your API key
node createAgent.js
# Copy the agent_id from the output
```

### Step 2: Add the Agent ID to Your Environment

Open your `.env` file and add the `BLAND_AGENT_ID` value you received from Step 1:

```
BLAND_API_KEY=sk-your-api-key-here
BLAND_AGENT_ID=your-agent-id-here
```

### Step 3: Run the Full Demo (Node.js)

```bash
cd node
node server.js
# Open http://localhost:3000 in your browser
```

Click "Start Conversation," allow microphone access, and talk to your AI agent.

## Step-by-Step Guide

### Step 1: Create a Web Agent

A web agent is a persistent configuration that defines how your AI assistant behaves. You create it once, and then authorize individual sessions against it. Think of it like a template for conversations.

The create agent script sends a POST request to `https://api.bland.ai/v1/agents` with your agent configuration:

```json
{
  "prompt": "You are a helpful customer support assistant for Acme Corp...",
  "voice": "mason",
  "first_sentence": "Hi there! How can I help you today?",
  "model": "base",
  "language": "ENG",
  "max_duration": 15,
  "interruption_threshold": 100
}
```

The API returns an `agent_id` that you will use for all future sessions.

### Step 2: Build a Session Token Endpoint

Your backend needs an endpoint that the frontend can call to get a session token. This endpoint:

1. Receives a request from the browser (optionally with user-specific data)
2. Calls `POST https://api.bland.ai/v1/agents/{agent_id}/authorize` with your API key
3. Returns the single-use `token` to the browser

The `request_data` field in the authorize request lets you pass dynamic information into the conversation. For example, you can include the user's name so the agent can greet them personally.

### Step 3: Build the Frontend

The frontend uses the `BlandWebClient` from the `bland-voice` package:

```javascript
import { BlandWebClient } from "bland-voice";

// Create a client instance with your agent ID and session token
const blandClient = new BlandWebClient(agentId, sessionToken);

// Start the voice conversation
await blandClient.initConversation({
  sampleRate: 44100
});
```

The `initConversation` method requests microphone access, establishes a WebSocket connection, and begins the voice session. The user can speak naturally, and the AI agent responds in real time.

## API Reference

### Create Web Agent

**Endpoint:** `POST https://api.bland.ai/v1/agents`

**Headers:**

| Header          | Value              | Description                    |
| --------------- | ------------------ | ------------------------------ |
| `Authorization` | `YOUR_API_KEY`     | Your Bland API key (no prefix) |
| `Content-Type`  | `application/json` | Required for JSON body         |

**Required Parameters:**

| Parameter | Type   | Description                                                                     |
| --------- | ------ | ------------------------------------------------------------------------------- |
| `prompt`  | string | Instructions that define how your AI agent behaves during conversations.        |

**Optional Parameters:**

| Parameter                | Type     | Default   | Description                                                                                                                   |
| ------------------------ | -------- | --------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `voice`                  | string   | `"mason"` | The voice the agent uses. Options include `"mason"`, `"maya"`, `"ryan"`, `"tina"`, `"josh"`, and more.                        |
| `first_sentence`         | string   | (auto)    | The opening phrase the agent says when the conversation starts. Maximum 200 characters. If omitted, the agent generates one.  |
| `language`               | string   | `"ENG"`   | Language code for the conversation. Default is English.                                                                        |
| `model`                  | string   | `"base"`  | Which model to use. `"base"` supports all features. `"turbo"` has the lowest latency.                                         |
| `analysis_schema`        | object   | (none)    | A JSON schema defining structured data to extract after each conversation ends.                                                |
| `tools`                  | array    | `[]`      | Custom API integrations the agent can invoke mid-conversation (e.g., CRM lookups, bookings).                                   |
| `dynamic_data`           | object   | (none)    | External API data that gets fetched and injected into the prompt before each conversation.                                     |
| `pathway_id`             | string   | (none)    | Use a conversational pathway instead of a freeform prompt. Overrides the `prompt` field.                                       |
| `interruption_threshold` | number   | `500`     | How patient the agent is before responding, in milliseconds. Lower values (50 to 200) make the agent more responsive.          |
| `max_duration`           | number   | `30`      | Maximum conversation length in minutes. The session ends automatically after this.                                             |
| `keywords`               | string[] | `[]`      | Words or phrases to boost transcription accuracy for (e.g., product names, technical terms).                                   |
| `webhook`                | string   | (none)    | A URL that receives a POST request with the full conversation data when the session ends.                                      |
| `metadata`               | object   | `{}`      | Custom key-value pairs for tracking and filtering. Returned in webhooks and call details.                                      |

**Success Response:**

```json
{
  "status": "success",
  "agent": {
    "agent_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "voice": "mason",
    "prompt": "You are a helpful customer support assistant...",
    "model": "base"
  }
}
```

### Authorize Web Agent Session

**Endpoint:** `POST https://api.bland.ai/v1/agents/{agent_id}/authorize`

**Headers:**

| Header          | Value              | Description                    |
| --------------- | ------------------ | ------------------------------ |
| `Authorization` | `YOUR_API_KEY`     | Your Bland API key (no prefix) |
| `Content-Type`  | `application/json` | Required for JSON body         |

**Parameters:**

| Parameter      | Type   | Description                                                                                                             |
| -------------- | ------ | ----------------------------------------------------------------------------------------------------------------------- |
| `request_data` | object | Dynamic variables passed into the agent prompt. Keys become template variables accessible via `{{key_name}}` syntax.    |

**Example Request:**

```json
{
  "request_data": {
    "name": "John",
    "account_type": "premium",
    "recent_order": "ORD-12345"
  }
```

If your agent prompt contains `"Hello {{name}}, I see you are a {{account_type}} member"`, those placeholders get replaced with the values you pass here.

**Success Response:**

```json
{
  "token": "single-use-session-token-string",
  "status": "success"
}
```

**Important:** Each token can only be used once. After a conversation starts with a given token, that token is invalidated. Request a new token for each conversation.

### BlandWebClient SDK

**Installation:**

```bash
npm install bland-voice
```

Or load via CDN in your HTML:

```html
<script src="https://cdn.jsdelivr.net/npm/bland-voice@latest/dist/bland-voice.min.js"></script>
```

**Usage:**

```javascript
// Import the client (ES module)
import { BlandWebClient } from "bland-voice";

// Create a new client with the agent ID and session token
const client = new BlandWebClient(agentId, sessionToken);

// Start the conversation (requests microphone access)
await client.initConversation({
  sampleRate: 44100  // Audio sample rate in Hz. 44100 is CD quality.
});

// End the conversation when done
client.stopConversation();
```

## Security Model

The web voice agent architecture is designed to keep your API key secure:

1. **API key stays server-side.** Your Bland API key is only used in backend requests. It is never sent to the browser or exposed in frontend code.

2. **Session tokens are single-use.** Each token authorizes exactly one conversation. Once used, it cannot be reused. If intercepted, the attacker gets at most one conversation.

3. **Tokens are short-lived.** Session tokens expire after a short period if not used, limiting the window of opportunity for misuse.

4. **Per-session data binding.** The `request_data` you pass during authorization is locked to that session. The frontend cannot modify it, ensuring data integrity.

## Verifying It Works

After running `server.js` and opening `http://localhost:3000`:

1. You should see a clean landing page with a "Start Conversation" button.
2. Clicking the button triggers a request to your `/authorize` endpoint. Check your server console for the log confirming the token was created.
3. The browser asks for microphone permission. Grant it.
4. The microphone animation appears, and the agent speaks its `first_sentence`.
5. Speak naturally. The agent responds in real time.
6. Click "End Conversation" to stop the session.

If anything goes wrong, check the browser developer console (F12) and your server terminal for error messages.

## Troubleshooting

### "Authorization header is missing or invalid"

Your API key is not being sent correctly. Double check that:
- Your `.env` file contains the correct key with no extra spaces or quotes.
- The key starts with the expected prefix (usually `sk-`).
- The `.env` file is in the correct directory.

### Microphone permission denied

The browser blocked microphone access. Make sure:
- You are serving the page over `http://localhost` or `https://`. Microphone access is not available on plain `file://` URLs.
- You have not previously blocked microphone access for the site. Check your browser settings to reset permissions.

### The agent does not respond

A few things to check:
- Confirm the `agent_id` in your `.env` file matches an existing agent.
- Check the browser console for WebSocket connection errors.
- Make sure your microphone is working (test it in another app first).
- Verify that the session token was successfully created by checking your server logs.

### "Module not found" errors

Make sure you have installed the dependencies:
- Python: `pip install requests python-dotenv`
- Node.js: `npm install axios dotenv express cors`

### The session token request fails

Check that:
- Your Bland account has sufficient credits.
- The `agent_id` exists and was created on the same account as your API key.
- Your server can reach `https://api.bland.ai` (no firewall blocking outbound requests).

## Next Steps

Now that you have a working web voice agent, explore these ideas:

- **Customize the prompt.** Tailor the agent for your specific use case, such as technical support, sales, or onboarding.
- **Pass user context.** Use `request_data` to personalize each session with the logged-in user's name, account details, or conversation history.
- **Add analysis.** Use `analysis_schema` to extract structured data from each conversation (e.g., sentiment, topics discussed, action items).
- **Integrate custom tools.** Let the agent call your APIs mid-conversation to look up orders, check inventory, or schedule appointments.
- **Use a pathway.** Replace the freeform prompt with a conversational pathway for more structured, multi-step interactions.
- **Add a webhook.** Set the `webhook` parameter to receive conversation data automatically when each session ends.

Check out the other cookbooks in this series for more advanced use cases like batch campaigns, appointment scheduling, and call analysis.
