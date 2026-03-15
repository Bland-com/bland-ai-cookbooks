# 01 - Getting Started with the Bland AI API

This cookbook walks you through making your first AI phone call with the Bland API. By the end, you will have sent a live phone call powered by an AI agent and retrieved the full transcript and summary.

## What You Will Build

A simple script that:

1. Sends an outbound phone call to a real phone number using an AI agent
2. Polls for the call to complete (optional)
3. Retrieves the call details, including the full transcript, summary, recording URL, and more

The example agent acts as a friendly restaurant reservation assistant for "Bella's Italian Kitchen," capable of booking tables, answering menu questions, and handling special requests.

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account.** Sign up at [app.bland.ai](https://app.bland.ai) if you do not have one.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.
- **A phone number to call.** You will need a real phone number in E.164 format (e.g., `+15551234567`). Use your own number for testing.

For the **Python** examples:
- Python 3.7 or later
- `requests` and `python-dotenv` packages

For the **Node.js** examples:
- Node.js 18 or later
- `axios` and `dotenv` packages

## Quick Start

### Python

```bash
cd python
pip install requests python-dotenv
cp .env.example .env
# Edit .env and add your API key and phone number
python send_call.py
# Copy the call_id from the output, then:
python get_call.py <call_id>
```

### Node.js

```bash
cd node
npm install axios dotenv
cp .env.example .env
# Edit .env and add your API key and phone number
node sendCall.js
# Copy the call_id from the output, then:
node getCall.js <call_id>
```

## Step-by-Step Guide

### Step 1: Get Your API Key

1. Log in to [app.bland.ai](https://app.bland.ai).
2. Navigate to **Settings > API Keys**.
3. Copy your API key. You will use this to authenticate every request.

### Step 2: Set Up Your Environment

Choose either Python or Node.js (or both). Copy the `.env.example` file to `.env` and fill in your credentials:

```
BLAND_API_KEY=sk-your-api-key-here
PHONE_NUMBER=+15551234567
```

Replace `+15551234567` with the real phone number you want the AI to call.

### Step 3: Send Your First Call

Run the send call script. This makes a POST request to the Bland API with your agent instructions, voice settings, and the target phone number. The API responds immediately with a `call_id` that you can use to track the call.

### Step 4: Retrieve Call Details

Once the call completes (usually within a few minutes), use the get call script with the `call_id` to fetch the full transcript, summary, recording URL, cost, and other metadata.

## API Reference

### Send Call

**Endpoint:** `POST https://api.bland.ai/v1/calls`

**Headers:**

| Header          | Value           | Description                     |
| --------------- | --------------- | ------------------------------- |
| `Authorization` | `YOUR_API_KEY`  | Your Bland API key (no prefix)  |
| `Content-Type`  | `application/json` | Required for JSON body       |

**Required Parameters:**

| Parameter      | Type   | Description                                                                 |
| -------------- | ------ | --------------------------------------------------------------------------- |
| `phone_number` | string | The phone number to call in E.164 format (e.g., `+15551234567`).           |
| `task`         | string | The prompt and instructions that define how your AI agent behaves on the call. |

**Optional Parameters:**

| Parameter                | Type    | Default      | Description                                                                                                          |
| ------------------------ | ------- | ------------ | -------------------------------------------------------------------------------------------------------------------- |
| `voice`                  | string  | `"mason"`    | The voice the agent uses. Options: `"mason"`, `"maya"`, `"ryan"`, `"tina"`, `"josh"`, `"florian"`, `"derek"`, `"june"`, `"nat"`, `"paige"`. |
| `first_sentence`         | string  | (auto)       | The exact sentence the agent says when the call connects. If omitted, the agent generates its own greeting.          |
| `model`                  | string  | `"base"`     | Which model to use. `"base"` supports all features. `"turbo"` has the lowest latency but may lack some features.     |
| `language`               | string  | `"babel-en"` | The language for the call. Supports 40+ languages. Default is English.                                               |
| `max_duration`           | integer | `30`         | Maximum call length in minutes. The call will automatically end after this duration.                                  |
| `record`                 | boolean | `false`      | Whether to record the call. When `true`, a `recording_url` will be available in the call details after completion.   |
| `temperature`            | float   | `0.7`        | Controls randomness in responses. `0` is deterministic, `1` is most creative. Range: 0 to 1.                        |
| `wait_for_greeting`      | boolean | `false`      | If `true`, the agent waits silently for the human to speak first before saying anything.                             |
| `transfer_phone_number`  | string  | (none)       | A phone number to transfer the call to if the human requests to speak with a real person.                            |
| `webhook`                | string  | (none)       | A URL that receives a POST request with the full call data when the call completes.                                  |
| `request_data`           | object  | `{}`         | Custom key-value pairs accessible in the prompt using `{{variable_name}}` syntax.                                    |
| `voicemail`              | object  | (default)    | Controls behavior when the call goes to voicemail. See voicemail options below.                                      |
| `background_track`       | string  | `null`       | Ambient background audio. Options: `null`, `"office"`, `"cafe"`, `"restaurant"`, `"none"`.                           |

**Voicemail Options:**

The `voicemail` parameter accepts an object with two fields:

```json
{
  "action": "hangup",
  "message": "Hi, this is Bella's calling about your reservation. Please call us back."
}
```

- `action` (string): What to do when voicemail is detected. Options: `"hangup"` (end the call), `"leave_message"` (leave the provided message), `"ignore"` (continue as if speaking to a person).
- `message` (string): The message to leave if `action` is `"leave_message"`.

**Using `request_data` (Dynamic Variables):**

You can pass custom data into your prompt using `request_data`. Any key-value pair you include becomes available in the `task` prompt via double curly braces:

```json
{
  "task": "You are calling {{customer_name}} about their reservation at {{time}}.",
  "request_data": {
    "customer_name": "Sarah",
    "time": "7:00 PM"
  }
}
```

**Success Response:**

```json
{
  "status": "success",
  "message": "Call successfully queued.",
  "call_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

### Get Call Details

**Endpoint:** `GET https://api.bland.ai/v1/calls/{call_id}`

**Headers:**

| Header          | Value          | Description                    |
| --------------- | -------------- | ------------------------------ |
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |

**Response Fields:**

| Field                    | Type    | Description                                                                                         |
| ------------------------ | ------- | --------------------------------------------------------------------------------------------------- |
| `call_id`                | string  | The unique identifier for this call.                                                                |
| `status`                 | string  | Current status of the call (e.g., `"completed"`, `"in-progress"`, `"queued"`).                      |
| `completed`              | boolean | Whether the call has finished.                                                                      |
| `call_length`            | float   | Duration of the call in minutes.                                                                    |
| `to`                     | string  | The phone number that was called.                                                                   |
| `from`                   | string  | The phone number the call was made from.                                                            |
| `transcripts`            | array   | Array of transcript objects, each with `text`, `user` (either `"agent"` or `"user"`), and timestamp.|
| `concatenated_transcript`| string  | The full transcript as a single string with speaker labels.                                         |
| `summary`                | string  | An AI-generated summary of the call.                                                                |
| `recording_url`          | string  | URL to the call recording (only available if `record` was `true`).                                  |
| `price`                  | float   | The cost of the call in USD.                                                                        |
| `variables`              | object  | Any variables that were set or extracted during the call.                                            |
| `answered_by`            | string  | Whether the call was answered by a `"human"` or `"voicemail"`.                                      |
| `queue_status`           | string  | The queue status of the call.                                                                       |
| `error_message`          | string  | If the call failed, this contains the error details. Otherwise `null`.                               |

## Verifying It Works

After running `send_call.py` (or `sendCall.js`), you should see output like:

```
Call successfully queued!
Call ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Your phone will ring within a few seconds. Answer it and have a conversation with the AI agent. After the call ends, run the get call script with the call ID to see the full transcript and summary.

You can also check the call status in the [Bland dashboard](https://app.bland.ai) under the Calls tab.

## Troubleshooting

### "Authorization header is missing or invalid"

Your API key is not being sent correctly. Double check that:
- Your `.env` file contains the correct key with no extra spaces or quotes.
- The key starts with the expected prefix (usually `sk-`).
- The `.env` file is in the same directory as the script you are running.

### "Invalid phone number"

The phone number must be in E.164 format. This means:
- It must start with `+` followed by the country code.
- US numbers look like `+15551234567` (11 digits total with the `+1` country code).
- No spaces, dashes, or parentheses.

### The call is queued but my phone never rings

A few things to check:
- Confirm the phone number is correct and can receive calls.
- Make sure your Bland account has sufficient credits.
- Check the call status using the get call script. The `error_message` field will contain details if something went wrong.
- Some carriers may block calls from unknown numbers. Try with a different phone.

### The call connects but the agent does not speak

This can happen if `wait_for_greeting` is set to `true`. The agent is waiting for you to say something first. Either speak first or set `wait_for_greeting` to `false`.

### "Module not found" errors

Make sure you have installed the dependencies:
- Python: `pip install requests python-dotenv`
- Node.js: `npm install axios dotenv`

### The transcript is empty

The transcript may take a few seconds to process after the call ends. Wait a moment and try fetching the call details again. If `record` was not set to `true`, the recording URL will also be unavailable.

## Next Steps

Now that you have made your first call, explore these ideas:

- **Customize the prompt.** Edit the `task` string to create different agent personas.
- **Try different voices.** Swap `"maya"` for `"mason"`, `"ryan"`, or any of the other available voices.
- **Add a webhook.** Set the `webhook` parameter to receive call data automatically when a call finishes, instead of polling.
- **Use dynamic variables.** Pass `request_data` to personalize each call with customer-specific information.
- **Enable recording.** Set `record` to `true` and retrieve the audio after the call.

Check out the other cookbooks in this series for more advanced use cases like batch calling, pathway-based agents, and inbound call handling.
