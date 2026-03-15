# 12 - SMS Messaging with Bland AI

This cookbook shows you how to send SMS messages, create AI-powered SMS conversations, combine voice calls with SMS follow-ups, and manage your messaging history using the Bland AI API. By the end, you will have sent a text message, launched an autonomous SMS agent, built a voice-to-SMS follow-up pipeline, and retrieved conversation logs.

## What You Will Build

Four scripts that demonstrate the core SMS capabilities:

1. **Send SMS** - Send a one-off text message to a phone number and see the response.
2. **Create SMS Conversation** - Launch an AI agent that carries on a multi-turn SMS conversation autonomously, following a prompt you define.
3. **SMS After Call** - The full voice-to-SMS workflow: make a phone call, extract structured data with an analysis schema, then automatically send a personalized SMS follow-up based on the call outcome.
4. **List Conversations** - Retrieve all SMS conversations on your account, with conversation IDs, phone numbers, message counts, and statuses.

The example conversation agent acts as a friendly appointment follow-up assistant for "Sunrise Dental," confirming upcoming appointments and answering patient questions via text. The SMS-after-call example shows an insurance renewal workflow where the agent calls to discuss policy changes, then texts a summary.

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account on the Enterprise plan.** SMS messaging is an Enterprise feature. Contact Bland sales or your account manager to enable it.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.
- **An SMS-configured phone number.** You need a Bland phone number that has been set up for SMS. You can check which numbers are SMS-enabled using the List SMS Numbers endpoint (`GET /v1/sms/numbers`).
- **A2P registration (for US numbers).** If you are sending SMS from a US phone number, you must complete A2P (Application-to-Person) 10DLC registration. This is a carrier requirement, not a Bland requirement. Your Bland account manager can help you through this process.
- **A recipient phone number.** You will need a real phone number that can receive text messages, in E.164 format (e.g., `+15551234567`). Use your own number for testing.

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
# Edit .env and add your API key, sender number, and recipient number
python send_sms.py
python create_conversation.py
python sms_after_call.py
python list_conversations.py
```

### Node.js

```bash
cd node
npm install axios dotenv
cp .env.example .env
# Edit .env and add your API key, sender number, and recipient number
node sendSms.js
node createConversation.js
node smsAfterCall.js
node listConversations.js
```

## Step-by-Step Guide

### Step 1: Get Your API Key

1. Log in to [app.bland.ai](https://app.bland.ai).
2. Navigate to **Settings > API Keys**.
3. Copy your API key. You will use this to authenticate every request.

### Step 2: Configure a Phone Number for SMS

Before you can send messages, you need a Bland phone number that supports SMS.

1. In the Bland dashboard, go to your phone numbers.
2. Select the number you want to use for SMS (or purchase a new one).
3. Enable SMS for that number. This is the same number you may already use for voice calls.
4. If you are using a US number, ensure you have completed A2P 10DLC registration (see the A2P Registration section below).

You can verify which numbers are SMS-enabled by calling the List SMS Numbers endpoint:

```
GET https://api.bland.ai/v1/sms/numbers
Authorization: YOUR_API_KEY
```

### Step 3: Set Up Your Environment

Choose either Python or Node.js (or both). Copy the `.env.example` file to `.env` and fill in your credentials:

```
BLAND_API_KEY=sk-your-api-key-here
FROM_NUMBER=+15551234567
TO_NUMBER=+15559876543
```

- `FROM_NUMBER` is your Bland phone number (the one configured for SMS).
- `TO_NUMBER` is the recipient's phone number.

### Step 4: Send a Test Message

Run the send SMS script. This sends a single text message from your Bland number to the recipient. You should receive the message on your phone within seconds.

### Step 5: Create an AI Conversation

Run the create conversation script. This launches an AI agent that will carry on a full SMS conversation with the recipient. The agent follows the prompt you provide and continues the conversation until completion.

### Step 6: List Your Conversations

Run the list conversations script to see all SMS conversations on your account, along with their statuses and message counts.

## Sending Messages

The simplest SMS operation is sending a single message. Use the Send SMS endpoint:

```
POST https://api.bland.ai/v1/sms/send
```

Required fields:
- `phone_number`: The recipient's phone number in E.164 format
- `from`: Your Bland phone number (must be SMS-configured)
- `message`: The text content to send

Optional fields:
- `pathway_id`: Attach a pathway to drive the conversation logic
- `wait`: If `true`, the API waits for a reply before responding

Each message costs **$0.02**, for both inbound and outbound messages.

## Creating AI-Powered Conversations

For ongoing, multi-turn conversations, use the Create SMS Conversation endpoint:

```
POST https://api.bland.ai/v1/sms/create
```

This creates an AI agent that autonomously manages the SMS conversation. The agent sends messages, processes replies, and follows your prompt instructions without any manual intervention.

Required fields:
- `phone_number`: The recipient's phone number
- `from`: Your Bland phone number
- `prompt`: The instructions for how the AI agent should behave

Optional fields:
- `pathway_id`: Use a pathway for conversation logic instead of a prompt
- `pathway_version`: Pin the conversation to a specific pathway version
- `node_id`: Start the conversation at a specific node in the pathway

The conversation has a lifecycle. The agent continues engaging until the conversation reaches a natural end or the pathway completes.

## Using Pathways with SMS

Pathways work with SMS the same way they work with voice calls. You can build a pathway in the Bland dashboard and reference it by `pathway_id` when creating an SMS conversation.

Key differences for SMS pathways:
- **Backchanneling is stripped automatically.** Pathway replies are cleaned of filler phrases (like "uh-huh", "right", "got it") that make sense in voice but feel unnatural in text.
- **Conversation pacing is asynchronous.** Unlike voice calls where the conversation flows in real time, SMS conversations happen at the recipient's pace.

To use a pathway, pass the `pathway_id` when creating the conversation:

```json
{
  "phone_number": "+15559876543",
  "from": "+15551234567",
  "pathway_id": "your-pathway-id-here"
}
```

## Syncing Voice and SMS Pathways

You can use the same pathway for both voice calls and SMS conversations. This is useful when you want consistent logic across channels.

- Build your pathway once in the Bland dashboard.
- Use the same `pathway_id` for both `POST /v1/calls` (voice) and `POST /v1/sms/create` (SMS).
- The pathway engine adapts its output for the channel: voice responses are spoken, SMS responses are sent as text with backchanneling removed.

This means you can handle a customer interaction over voice and follow up via SMS using the exact same conversation logic.

## Voice Call + SMS Follow-Up Workflow

One of the most powerful patterns in Bland is combining voice calls with automated SMS follow-ups. The `sms_after_call` / `smsAfterCall` scripts demonstrate this end-to-end:

**How it works:**

1. Send a phone call with an `analysis_schema` that defines the structured data you want to extract (customer name, preferences, action items).
2. After the call completes, read the analysis results.
3. Build a personalized SMS message based on what was discussed.
4. Send the SMS to the customer as a follow-up.

**Example: Insurance renewal call with SMS summary**

The included example simulates an insurance agent calling about a policy renewal. During the call, the agent discusses coverage changes and bundle discounts. After the call, the script:

- Extracts whether the customer wants changes, what they requested, and whether they are interested in bundling policies.
- Builds a tailored SMS summarizing the conversation and next steps.
- Sends the SMS automatically.

**The analysis_schema for this workflow:**

```json
{
  "customer_name": "The customer's name.",
  "wants_changes": "Does the customer want changes? true or false.",
  "requested_changes": "What changes they requested. Null if none.",
  "interested_in_bundle": "Interested in a bundle discount? true, false, or maybe.",
  "has_questions": "Any unresolved questions? true or false.",
  "question_summary": "Summary of their questions. Null if none."
}
```

**In production**, you would not poll for the call to complete. Instead, use a post-call webhook. When the webhook fires, your server reads the `analysis` object from the payload and sends the SMS immediately. This makes the entire flow event-driven with zero manual intervention.

```
Call completes -> Webhook fires -> Read analysis -> Send SMS -> Done
```

This pattern works for any industry: appointment confirmations, sales follow-ups, support ticket summaries, or onboarding check-ins.

## A2P Registration Requirements

If you are sending SMS messages from US phone numbers, carriers require A2P (Application-to-Person) 10DLC registration. This is an industry-wide regulation, not specific to Bland.

**What is A2P 10DLC?**
A2P 10DLC allows businesses to send application-generated text messages over standard 10-digit long code phone numbers. Registration ensures your messages are not flagged as spam by carriers.

**How to register:**
1. Contact your Bland account manager or reach out to Bland support.
2. Bland will guide you through the registration process, which involves providing your business details and describing your messaging use case.
3. Registration typically takes a few business days to approve.

**What happens without registration?**
Unregistered messages from US numbers may be blocked or filtered by carriers. Your messages might not be delivered, or delivery rates may be very low.

## RCS Support

Bland SMS supports RCS (Rich Communication Services) when available. RCS is the next-generation messaging standard that enhances SMS with features like:

- Read receipts
- Typing indicators
- Higher-quality media
- Rich cards and carousels

**How it works:**
- Bland automatically upgrades messages to RCS when the recipient's device and carrier support it.
- If RCS is not available, the message falls back to standard SMS.
- You do not need to change anything in your API calls. The upgrade happens transparently.

This means your messages will look richer and more modern on supported devices, with no extra configuration on your part.

## Analyzing Conversations

You can analyze completed SMS conversations using the Analyze endpoint:

```
POST https://api.bland.ai/v1/sms/analyze
```

Pass a `conversation_id`, a `goal`, and a list of `questions` to extract structured insights from the conversation.

## Additional Endpoints

### Get a Single Conversation

```
GET https://api.bland.ai/v1/sms/conversations/{conversation_id}
```

Returns the full conversation details, including all messages exchanged.

### Update SMS Configuration

```
POST https://api.bland.ai/v1/sms/update
```

Configure SMS settings for a specific phone number, such as enabling or disabling SMS, setting default prompts, or attaching pathways.

### List SMS Numbers

```
GET https://api.bland.ai/v1/sms/numbers
```

Returns all phone numbers on your account that are configured for SMS.

## Pricing

SMS messaging is billed per message:

| Direction | Cost per Message |
| --------- | ---------------- |
| Outbound  | $0.02            |
| Inbound   | $0.02            |

Both messages sent by your agent and replies received from the recipient count as billable messages. For example, a 10-message conversation (5 sent, 5 received) would cost $0.20.

## Verifying It Works

The easiest way to verify everything is working:

1. **Send yourself a test message.** Use `send_sms.py` or `sendSms.js` with your own phone number as the recipient. You should receive the text within a few seconds.

2. **Create a test conversation.** Run `create_conversation.py` or `createConversation.js` to start an AI conversation with yourself. Reply to the text messages and watch the agent respond.

3. **Check the dashboard.** Log in to [app.bland.ai](https://app.bland.ai) and look at the SMS section to see your messages and conversations.

4. **List conversations.** Run `list_conversations.py` or `listConversations.js` to confirm your conversations appear in the API response.

## Troubleshooting

### "Authorization header is missing or invalid"

Your API key is not being sent correctly. Double check that:
- Your `.env` file contains the correct key with no extra spaces or quotes.
- The key starts with the expected prefix (usually `sk-`).
- The `.env` file is in the same directory as the script you are running.

### "Invalid phone number"

The phone number must be in E.164 format:
- It must start with `+` followed by the country code.
- US numbers look like `+15551234567` (11 digits total with the `+1` country code).
- No spaces, dashes, or parentheses.

### Messages are not being delivered

A few things to check:
- Confirm the `from` number is SMS-configured in the Bland dashboard.
- If you are using a US number, make sure A2P 10DLC registration is complete.
- Check your Bland account for sufficient credits.
- The recipient's carrier may be filtering messages. Try a different recipient number.

### "SMS is not enabled for this number"

The phone number you are using as the sender has not been configured for SMS. Go to the Bland dashboard, select the phone number, and enable SMS.

### "Feature not available on your plan"

SMS messaging is an Enterprise feature. Contact Bland sales or your account manager to upgrade your plan.

### "Module not found" errors

Make sure you have installed the dependencies:
- Python: `pip install requests python-dotenv`
- Node.js: `npm install axios dotenv`

## Limitations and Upcoming Features

**Current limitations:**
- SMS is only available on Enterprise plans.
- A2P 10DLC registration is required for US phone numbers.
- MMS (multimedia messaging) support varies by carrier and region.
- Message length follows standard SMS limits (160 characters for GSM-7 encoding, 70 characters for Unicode). Longer messages are automatically split into multiple segments but still count as one API message.

**Upcoming features:**
- Scheduled messages (send a message at a future time)
- Conversation templates for common use cases
- Enhanced analytics and reporting for SMS campaigns
- Expanded international carrier support

## Next Steps

Now that you have SMS messaging working, explore these ideas:

- **Build a pathway for SMS.** Create a multi-step conversation flow in the Bland dashboard and reference it with `pathway_id`.
- **Sync voice and SMS.** Use the same pathway for both phone calls and text messages to create a unified customer experience.
- **Analyze conversations.** Use the Analyze endpoint to extract structured data from completed conversations.
- **Set up webhooks.** Configure webhooks to get notified when new messages arrive or conversations complete.
- **Combine with voice.** Start a conversation with a phone call and follow up via SMS using the same pathway logic.

Check out the other cookbooks in this series for more advanced use cases like batch campaigns, pathway-based agents, and call analysis.
