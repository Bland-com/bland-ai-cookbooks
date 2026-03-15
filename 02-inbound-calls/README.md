# Cookbook 02: Inbound Calls

Let your AI agent answer the phone. In this cookbook you will buy a phone number from Bland AI, configure an AI agent to handle incoming calls, and verify everything works by calling the number yourself.

## Why Inbound Calls Matter

Outbound calls are great for reaching out, but most businesses also need to *receive* calls. Think customer support lines, appointment booking, after-hours answering services, and intake hotlines. With Bland AI inbound calls, you get a phone number that an AI agent answers 24/7, following whatever instructions you give it.

The flow is simple:

1. **Purchase a phone number** from Bland AI ($15/month).
2. **Configure an AI agent** on that number with a prompt, voice, greeting, and any advanced settings you need.
3. **Callers dial the number** and talk to your AI agent in real time.

## Prerequisites

- A Bland AI account with credits ([app.bland.ai](https://app.bland.ai))
- Your API key from the developer portal
- Python 3.7+ or Node.js 16+

### Python

```bash
pip install requests python-dotenv
```

### Node.js

```bash
npm init -y
npm install axios dotenv
```

## Quick Start

### Step 1: Set Up Your Environment

Copy the `.env.example` file in either the `python/` or `node/` folder and rename it to `.env`. Then paste in your API key:

```
BLAND_API_KEY=sk-your-api-key-here
```

### Step 2: Purchase a Phone Number

Run the purchase script to buy a number. By default it grabs a number with a 415 (San Francisco) area code, but you can change this in the script.

**Python:**
```bash
cd python
python purchase_number.py
```

**Node.js:**
```bash
cd node
node purchaseNumber.js
```

The response will include your new phone number. Copy it for the next step.

### Step 3: Configure the Inbound Agent

Open `configure_inbound.py` (or `configureInbound.js`) and paste your new phone number into the `INBOUND_NUMBER` variable at the top of the file. Then run it:

**Python:**
```bash
python configure_inbound.py
```

**Node.js:**
```bash
node configureInbound.js
```

This sends your agent configuration (prompt, voice, greeting, transfer numbers, and more) to the Bland API. Once it succeeds, your number is live.

### Step 4: Test It

Call the number from your personal phone. You should hear your agent greet you with the `first_sentence` you configured, then carry on a conversation following the prompt.

### Step 5: List Your Numbers

At any time you can list all the inbound numbers on your account and see their current configurations:

**Python:**
```bash
python list_numbers.py
```

**Node.js:**
```bash
node listNumbers.js
```

## API Reference

### Purchase a Phone Number

```
POST https://api.bland.ai/v1/inbound/purchase
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `area_code` | string | `"415"` | Three-digit US/CA area code for your new number |
| `country_code` | string | `"US"` | Country code. Supported values: `"US"` or `"CA"` |
| `phone_number` | string | *none* | (Optional) Request a specific number in `"+12223334444"` format |

**Cost:** $15/month subscription per number, billed automatically.

### Configure an Inbound Number

```
POST https://api.bland.ai/v1/inbound/{phone_number}
```

Replace `{phone_number}` with your purchased number (e.g., `+14155551234`).

#### Core Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | string | The main instructions for your AI agent. This is the most important parameter. Tell the agent who it is, what it should do, and how to handle different situations. |
| `voice` | string | Which voice the agent uses. Try `"mason"`, `"josh"`, `"emma"`, or `"tina"`. |
| `first_sentence` | string | The opening greeting callers hear when the agent picks up. |
| `model` | string | `"base"` for cost-effective calls, `"turbo"` for faster responses. |
| `language` | string | Language code (e.g., `"en"` for English, `"es"` for Spanish). |
| `max_duration` | integer | Maximum call length in minutes. The agent hangs up when this limit is reached. |
| `record` | boolean | Set to `true` to record the call audio for later review. |

#### Call Transfer Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `transfer_phone_number` | string | A single phone number to transfer callers to when the agent decides a human is needed. |
| `transfer_list` | object | A map of department names to phone numbers for multi-destination routing (see example below). |

**Transfer list example:**

```json
{
  "Sales": "+14155559999",
  "Support": "+14155558888",
  "Billing": "+14155557777"
}
```

When you include a `transfer_list`, the agent can ask the caller which department they need and route them accordingly. Just mention the available departments in your prompt so the agent knows they exist.

#### Advanced Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `webhook` | string | A URL that Bland will POST to after each call ends, containing the transcript, metadata, and any extracted data. |
| `tools` | array | Custom tools (function calls) the agent can invoke mid-conversation, such as looking up an order or booking an appointment. |
| `request_data` | object | Key-value pairs of custom variables you want available in the prompt via `{{variable_name}}` syntax. |
| `background_track` | string | Ambient audio played behind the agent's voice. Options include `"office"`, `"convention_hall"`, and others. |
| `interruption_threshold` | number | Controls how patient the agent is before it considers itself interrupted. Range: 50 to 200. Lower values mean the agent pauses more easily when the caller speaks. |
| `block_interruptions` | boolean | If `true`, the agent finishes its sentence before listening, ignoring mid-sentence interruptions entirely. |
| `noise_cancellation` | boolean | Filters out background noise from the caller's environment for cleaner transcription. |
| `keywords` | string[] | Words or phrases to boost in the transcription model. Useful for brand names, technical terms, or uncommon words the caller might say. |
| `analysis_schema` | object | A schema describing what data to extract from the call after it ends. Each key is a field name and each value is a description of what to extract. |
| `fallback_number` | string | A phone number to redirect calls to if you ever need to take the agent offline for maintenance. |

### List Inbound Numbers

```
GET https://api.bland.ai/v1/inbound
```

No parameters required. Returns an array of all your inbound numbers and their current configurations.

## Setting Up Call Transfers

Call transfers are one of the most valuable features for inbound agents. Here is the recommended approach:

1. **Define your transfer list** with department names and real phone numbers.
2. **Mention the departments in your prompt** so the agent knows what options are available.
3. **Give the agent instructions** on when to transfer (e.g., "If the caller asks for billing help, transfer them to Billing").

The example in `configure_inbound.py` / `configureInbound.js` demonstrates a receptionist agent with three departments: Sales, Support, and Billing. The agent asks what the caller needs, then routes them to the right team.

## Common Issues

### "Number not found" when configuring
Make sure you include the full number with country code and the `+` prefix (e.g., `+14155551234`). The number must also be one you have purchased on your account.

### Agent does not answer
Double-check that you have called the correct number and that your configuration request returned a success response. You can verify by running the list numbers script and confirming the number appears with the right prompt.

### Agent sounds robotic or unnatural
Try switching to `"turbo"` model for faster, more natural responses. Also experiment with different voices. `"mason"` and `"josh"` tend to work well for professional use cases.

### Caller gets cut off too early
Increase the `max_duration` parameter. The default might be too short for longer conversations.

### Transfer is not working
Confirm that the numbers in your `transfer_list` are valid, formatted with the `+` country code prefix, and that the receiving lines are able to accept incoming calls.

### Background noise causing issues
Enable `noise_cancellation` in your configuration to filter out ambient sound from the caller's side.

## Files in This Cookbook

```
02-inbound-calls/
  README.md               <- You are here
  python/
    .env.example           <- Template for your API key
    purchase_number.py     <- Buy a phone number
    configure_inbound.py   <- Set up the AI agent on your number
    list_numbers.py        <- List all your inbound numbers
  node/
    .env.example           <- Template for your API key
    purchaseNumber.js      <- Buy a phone number
    configureInbound.js    <- Set up the AI agent on your number
    listNumbers.js         <- List all your inbound numbers
```

## Next Steps

Once your inbound agent is live, consider:

- Adding **custom tools** so the agent can look up order status or check appointment availability mid-call (see [Cookbook 04](../04-custom-tools/))
- Setting up a **webhook** to push call data to your CRM or analytics platform (see [Cookbook 10](../10-call-analysis/))
- Building a **Conversational Pathway** for complex multi-step call flows (see [Cookbook 03](../03-pathways/))
