# 05 - Web Chat Widget

This cookbook shows you how to create and embed a Bland AI chat widget on any website. The widget gives your visitors an AI-powered chat assistant that lives in the corner of your page, handles conversations autonomously, and can escalate to a live human agent when needed.

## What You Will Build

1. A **widget configuration** created via the Bland API, defining the agent's personality, voice, and behavior
2. A **complete HTML page** with the widget embedded, demonstrating a realistic SaaS landing page with AI chat support
3. Understanding of **custom components**, **live agent escalation**, and **post-conversation webhooks**

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account.** Sign up at [app.bland.ai](https://app.bland.ai) if you do not have one.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.

For the **Python** example:
- Python 3.7 or later
- `requests` and `python-dotenv` packages

For the **Node.js** example:
- Node.js 18 or later
- `axios` and `dotenv` packages

## Quick Start

### Step 1: Create a Widget via the API

#### Python

```bash
cd python
pip install requests python-dotenv
cp .env.example .env
# Edit .env and add your API key
python create_widget.py
```

#### Node.js

```bash
cd node
npm install axios dotenv
cp .env.example .env
# Edit .env and add your API key
node createWidget.js
```

Both scripts will print a `widget_id`. Copy it for the next step.

### Step 2: Embed the Widget on Your Page

Open `index.html` in a text editor and replace `YOUR_WIDGET_ID` with the widget ID from Step 1. Then open the file in a browser or serve it from any web server to see the widget in action.

## How It Works

### Creating a Widget

The Bland API exposes a single endpoint for creating chat widgets:

**Endpoint:** `POST https://api.bland.ai/v1/widget`

**Headers:**

| Header          | Value            | Description                    |
| --------------- | ---------------- | ------------------------------ |
| `Authorization` | `YOUR_API_KEY`   | Your Bland API key (no prefix) |
| `Content-Type`  | `application/json` | Required for JSON body       |

**Body Parameters:**

| Parameter      | Type   | Required | Description                                                                 |
| -------------- | ------ | -------- | --------------------------------------------------------------------------- |
| `prompt`       | string | Yes      | The system prompt defining the agent's behavior and personality.            |
| `voice`        | string | No       | The voice for the agent. Same voice options as phone calls.                 |
| `first_sentence` | string | No    | The greeting message the agent sends when a conversation starts.            |
| `pathway_id`   | string | No       | If using a Conversational Pathway, the pathway ID to follow.                |
| `tools`        | array  | No       | Custom tools the agent can invoke mid-conversation (API calls, lookups).    |
| `model`        | string | No       | The model to use (`"base"` or `"turbo"`).                                   |
| `temperature`  | float  | No       | Controls response randomness. 0 is deterministic, 1 is most creative.      |

**Success Response:**

```json
{
  "status": "success",
  "widget_id": "wdg_xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Embedding the Widget

Once you have a `widget_id`, add two script tags to your HTML page's `<head>`:

```html
<script>
  window.blandSettings = {
    widget_id: "YOUR_WIDGET_ID"
  };
</script>
<script src="https://widget.bland.ai/loader.js" defer></script>
```

That is all you need for a basic setup. The widget will appear as a chat bubble in the bottom-right corner of your page.

## Configuration Options

The `window.blandSettings` object accepts the following properties:

### widget_id (string, required)

The unique identifier for your widget, returned by the Create Widget API.

```javascript
window.blandSettings = {
  widget_id: "wdg_abc123"
};
```

### request_data (object)

Custom key-value pairs that personalize the conversation. These values become accessible in your widget's prompt using `{{variable_name}}` syntax.

For example, if your prompt contains `"Hello {{first_name}}, welcome back!"` and you pass the following `request_data`, the agent will greet the user by name:

```javascript
window.blandSettings = {
  widget_id: "wdg_abc123",
  request_data: {
    user_id: "12345",
    first_name: "John",
    plan: "enterprise",
    company: "Acme Corp"
  }
};
```

This is useful for logged-in users. You can pull data from your authentication system and pass it directly into the widget so the agent already knows who it is talking to.

### default_chat (boolean, default: false)

Controls what happens when the widget button is clicked.

- `false` (default): Shows a channel selection menu first (e.g., chat, voice, or other channels you have configured).
- `true`: Opens the chat conversation immediately, skipping the channel menu.

```javascript
window.blandSettings = {
  widget_id: "wdg_abc123",
  default_chat: true
};
```

### visitor_id (string)

A custom identifier for the visitor. By default, Bland uses a cookie-based ID that expires after one week. Setting `visitor_id` lets you use your own tracking system so conversations persist across devices or sessions.

```javascript
window.blandSettings = {
  widget_id: "wdg_abc123",
  visitor_id: "user-98765"
};
```

### enable_widget_state_events (boolean, default: false)

When `true`, the widget emits custom DOM events whenever its state changes (opened, closed, minimized, etc.). You can listen for these events to trigger your own UI logic:

```javascript
window.blandSettings = {
  widget_id: "wdg_abc123",
  enable_widget_state_events: true
};

// Listen for widget state changes
window.addEventListener("bland-widget-state", function(event) {
  console.log("Widget state changed:", event.detail);
});
```

### draggable (boolean, default: false)

When `true`, the user can click and drag the widget button to reposition it on the page. Useful if the default bottom-right position overlaps with other UI elements.

```javascript
window.blandSettings = {
  widget_id: "wdg_abc123",
  draggable: true
};
```

### Full Configuration Example

```javascript
window.blandSettings = {
  widget_id: "wdg_abc123",
  request_data: {
    user_id: "12345",
    first_name: "John",
    plan: "enterprise"
  },
  default_chat: true,
  visitor_id: "user-12345",
  enable_widget_state_events: true,
  draggable: false
};
```

## Custom Components

Custom components let you display rich UI elements at specific points during a conversation. They are rendered as embedded iframes inside the chat window.

### How They Work

1. You define a custom component URL in your widget configuration or pathway.
2. At the appropriate point in the conversation, the widget loads your component URL as an iframe.
3. Any variables from the conversation are passed to your component as URL query parameters.
4. Your component can send messages back to the chat using `postMessage`.

### Passing Variables to Components

If the conversation has variables like `product_name` and `price`, your component URL will be loaded as:

```
https://your-site.com/component.html?product_name=Widget+Pro&price=49.99
```

You can read these values in your component with standard JavaScript:

```javascript
const params = new URLSearchParams(window.location.search);
const productName = params.get("product_name");
const price = params.get("price");
```

### Sending Messages Back to the Chat

Your custom component can inject messages into the conversation by calling `postMessage` on the parent window. Every message must be prefixed with `widget-message:` so the widget knows to treat it as a chat message.

```javascript
// Send a message from your custom component back into the chat
parent.window.postMessage("widget-message:The user selected the Pro plan at $49/month", "*");
```

This message will appear in the conversation as if the user typed it, allowing the agent to respond accordingly.

### Example Custom Component

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: sans-serif; padding: 16px; }
    button {
      background: #4F46E5;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 6px;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <h3>Choose a Plan</h3>
  <button onclick="selectPlan('starter')">Starter ($19/mo)</button>
  <button onclick="selectPlan('pro')">Pro ($49/mo)</button>

  <script>
    function selectPlan(plan) {
      // Send the selection back to the chat conversation
      parent.window.postMessage("widget-message:I would like the " + plan + " plan", "*");
    }
  </script>
</body>
</html>
```

## Live Agent Escalation

The widget supports handing off conversations to a live human agent when the AI determines it cannot resolve the issue on its own. Bland integrates with popular support platforms and also supports custom webhooks.

### Supported Platforms

- **Zendesk**
- **Intercom**
- **Freshdesk**
- **Custom platforms** (via webhooks)

### Webhook-Based Escalation

When using custom webhooks for live agent handoff, Bland sends two types of webhook events:

#### INITIAL_CONVERSATION

Sent when a conversation is first transferred to a live agent. The payload includes the complete conversation history up to the point of transfer.

```json
{
  "type": "INITIAL_CONVERSATION",
  "conversation_id": "conv_abc123",
  "visitor_id": "user-12345",
  "messages": [
    { "role": "agent", "content": "Hi! How can I help you today?" },
    { "role": "user", "content": "I need to talk to a real person." },
    { "role": "agent", "content": "Let me connect you with a team member right away." }
  ],
  "metadata": {
    "request_data": {
      "user_id": "12345",
      "first_name": "John"
    }
  }
}
```

#### MESSAGE

Sent for each subsequent message the visitor sends after the handoff. Your live agent platform receives these in real time.

```json
{
  "type": "MESSAGE",
  "conversation_id": "conv_abc123",
  "visitor_id": "user-12345",
  "content": "Are you still there?"
}
```

### HMAC Signature Verification

Every webhook request includes an `X-Bland-Signature` header containing an HMAC-SHA256 signature. Use this to verify that the request genuinely came from Bland and was not tampered with.

```python
import hmac
import hashlib

def verify_signature(payload_body, signature, secret):
    expected = hmac.new(
        secret.encode("utf-8"),
        payload_body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Responding to the Visitor

After a live agent composes a reply, send it back to the visitor using the Bland **Send Live Agent Message** endpoint. The message will appear in the widget chat in real time.

## Post-Conversation Webhooks

You can configure a webhook URL to receive a notification when a widget conversation ends. This is useful for logging, analytics, CRM updates, or triggering follow-up workflows.

### When Conversations End

A conversation is considered "ended" when:

- The visitor explicitly closes the chat.
- The conversation times out after a period of inactivity.

The default inactivity timeout is **24 hours**. You can change this with the `config.timeoutSeconds` parameter when creating your widget.

### Webhook Payload

```json
{
  "conversation_id": "conv_abc123",
  "widget_id": "wdg_abc123",
  "visitor_id": "user-12345",
  "started_at": "2025-01-15T10:30:00Z",
  "ended_at": "2025-01-15T10:45:00Z",
  "end_reason": "visitor_closed",
  "messages": [
    { "role": "agent", "content": "Hi! How can I help you?" },
    { "role": "user", "content": "I have a billing question." },
    { "role": "agent", "content": "I would be happy to help with billing. What is your account email?" }
  ],
  "metadata": {
    "request_data": {
      "user_id": "12345",
      "first_name": "John"
    }
  }
}
```

### Payload Fields

| Field             | Type   | Description                                                                          |
| ----------------- | ------ | ------------------------------------------------------------------------------------ |
| `conversation_id` | string | Unique identifier for the conversation.                                              |
| `widget_id`       | string | The widget this conversation belongs to.                                             |
| `visitor_id`      | string | The visitor's ID (custom or cookie-based).                                           |
| `started_at`      | string | ISO 8601 timestamp of when the conversation started.                                 |
| `ended_at`        | string | ISO 8601 timestamp of when the conversation ended.                                   |
| `end_reason`      | string | Why the conversation ended: `"visitor_closed"`, `"timeout"`, or `"agent_closed"`.    |
| `messages`        | array  | The full conversation history with role and content for each message.                 |
| `metadata`        | object | Any `request_data` that was passed when the widget loaded.                           |

## Full Example HTML Page

The `index.html` file in this cookbook is a complete, working demo. It simulates a SaaS product landing page with the Bland chat widget embedded in the corner. To use it:

1. Run `create_widget.py` or `createWidget.js` to get a `widget_id`.
2. Open `index.html` and replace `YOUR_WIDGET_ID` with your actual widget ID.
3. Open the file in a browser.
4. Click the chat bubble in the bottom-right corner to start a conversation.

## Troubleshooting

### The widget does not appear on my page

Make sure:
- The `widget_id` in `window.blandSettings` is correct.
- The loader script tag has the `defer` attribute.
- You are not blocking third-party scripts with a content security policy or ad blocker.

### The widget appears but conversations do not start

- Check the browser console for errors.
- Verify your API key is valid and your account has credits.
- Make sure the widget was created successfully (the create script should print a widget ID).

### request_data variables are not being replaced in the prompt

- Confirm the variable names in `request_data` match the `{{variable_name}}` placeholders in your prompt exactly (case-sensitive).
- Make sure `request_data` is set in `window.blandSettings` before the loader script runs.

### Custom components are not loading

- The component URL must be publicly accessible (not localhost, unless testing locally).
- Check the browser console for iframe-related errors.
- Ensure your component page does not block being embedded in an iframe (check `X-Frame-Options` headers).

### Live agent messages are not appearing in the chat

- Verify your webhook endpoint is reachable and returning 200 status codes.
- Check the `X-Bland-Signature` verification logic.
- Make sure you are using the correct Send Live Agent Message endpoint to reply.

## Next Steps

- **Customize the look and feel.** Adjust colors, position, and greeting messages to match your brand.
- **Add custom components.** Build interactive forms, product selectors, or scheduling UIs that appear inline in the chat.
- **Set up live agent escalation.** Connect Zendesk, Intercom, Freshdesk, or your own support platform.
- **Track conversations.** Use post-conversation webhooks to pipe chat data into your analytics or CRM.
- **Combine with Pathways.** Use the `pathway_id` parameter to power your widget with a Conversational Pathway for complex, multi-step interactions.

Check out the other cookbooks in this series for phone-based agents, batch campaigns, SMS messaging, and more.
