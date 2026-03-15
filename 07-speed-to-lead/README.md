# 07 - Speed to Lead with Bland AI

This cookbook shows you how to build an instant lead-calling system that contacts new leads within seconds of form submission. When a prospect fills out a form on your website, your server fires off a Bland AI call immediately, qualifying the lead, answering questions, and optionally transferring hot prospects to a live sales rep or booking a demo.

## Why Speed to Lead Matters

Speed to lead is the practice of contacting new leads as quickly as possible after they express interest. Research consistently shows that response time is the single biggest factor in lead conversion:

- Calling within **5 minutes** of an inquiry increases conversion rates by **400%** compared to calling after 10 minutes.
- After 30 minutes, the odds of qualifying a lead drop by **21x**.
- **78% of buyers** purchase from the company that responds first.

The problem is that human sales reps cannot respond instantly, 24 hours a day, 7 days a week. They are in meetings, on other calls, or off the clock. Bland AI solves this by providing an AI agent that never sleeps, responds in seconds, and can handle unlimited concurrent calls. Every lead gets an immediate, personalized phone call, whether it is 2 PM on a Tuesday or 3 AM on a Sunday.

## What You Will Build

A complete speed-to-lead system with two components:

1. **Lead Caller** (`lead_caller.py` / `leadCaller.js`): A function that takes lead data and instantly triggers a Bland AI qualification call.
2. **Webhook Receiver** (`webhook_receiver.py` / `webhookReceiver.js`): A web server with two endpoints:
   - `POST /webhook/lead-form`: Receives form submissions and triggers calls immediately.
   - `POST /webhook/call-complete`: Receives post-call data from Bland and processes the qualification results.

## Architecture

Here is how the full system works end to end:

```
+------------------+        +-------------------+        +----------------+
|                  |  POST  |                   |  POST  |                |
|  Lead fills out  +------->+  Your Webhook     +------->+  Bland AI API  |
|  web form        |        |  Server           |        |  /v1/calls     |
|  (Typeform,      |        |  /webhook/        |        |                |
|   HubSpot, etc.) |        |  lead-form        |        +-------+--------+
|                  |        |                   |                |
+------------------+        +-------------------+                |
                                                                 |
                            AI calls the lead                    |
                            within seconds                       |
                                                                 v
+------------------+        +-------------------+        +----------------+
|                  |        |                   |  POST  |                |
|  CRM updated     +<------+  Your Webhook     +<------+  Bland AI      |
|  with call       |        |  Server           |        |  sends post-   |
|  results         |        |  /webhook/        |        |  call webhook  |
|                  |        |  call-complete    |        |                |
+------------------+        +-------------------+        +----------------+

                                    |
                                    v (if qualified)
                            +----------------+
                            |                |
                            |  Transfer to   |
                            |  sales rep or  |
                            |  book a demo   |
                            |                |
                            +----------------+
```

**Step by step:**

1. A lead fills out a form on your website (or through Typeform, HubSpot, Calendly, etc.).
2. The form sends a POST request to your webhook server at `/webhook/lead-form`.
3. Your server instantly calls the Bland AI API to trigger an outbound call to the lead.
4. The AI agent greets the lead by name, references their interest, and asks qualifying questions.
5. If the lead is qualified, the agent transfers them to a live sales rep or books a demo.
6. If the call goes to voicemail, the agent leaves a personalized message.
7. When the call ends, Bland sends a POST request to your `/webhook/call-complete` endpoint with the full transcript, summary, and extracted variables.
8. Your server processes the results and pushes them to your CRM.

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account.** Sign up at [app.bland.ai](https://app.bland.ai) if you do not have one.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.
- **A phone number to test with.** Use your own number in E.164 format (e.g., `+15551234567`).
- **A publicly accessible server** (or use [ngrok](https://ngrok.com) for local testing) to receive webhooks.

For the **Python** examples:
- Python 3.7 or later
- `requests`, `flask`, and `python-dotenv` packages

For the **Node.js** examples:
- Node.js 18 or later
- `axios`, `express`, and `dotenv` packages

## Quick Start

### Python

```bash
cd python
pip install requests flask python-dotenv
cp .env.example .env
# Edit .env with your API key, webhook URL, and transfer number
python webhook_receiver.py
```

In a separate terminal (or use curl):

```bash
# Simulate a lead form submission
curl -X POST http://localhost:5000/webhook/lead-form \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "phone": "+15551234567",
    "email": "jane@example.com",
    "source": "Website Contact Form",
    "interest": "Enterprise Plan"
  }'
```

### Node.js

```bash
cd node
npm install axios express dotenv
cp .env.example .env
# Edit .env with your API key, webhook URL, and transfer number
node webhookReceiver.js
```

In a separate terminal:

```bash
# Simulate a lead form submission
curl -X POST http://localhost:3000/webhook/lead-form \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "phone": "+15551234567",
    "email": "jane@example.com",
    "source": "Website Contact Form",
    "interest": "Enterprise Plan"
  }'
```

## Step-by-Step Guide

### Step 1: Set Up Your Environment

Copy `.env.example` to `.env` in the `python/` or `node/` directory and fill in your values:

```
BLAND_API_KEY=sk-your-api-key-here
WEBHOOK_URL=https://your-server.com/webhook/call-complete
TRANSFER_NUMBER=+15559876543
SALES_NUMBER=+15559876543
SUPPORT_NUMBER=+15551112222
```

- `BLAND_API_KEY`: Your Bland API key from the dashboard.
- `WEBHOOK_URL`: The public URL where Bland will send post-call results. If testing locally, use ngrok to expose your local server.
- `TRANSFER_NUMBER`: The default phone number for transferring qualified leads to a sales rep.
- `SALES_NUMBER`: Dedicated sales line for the transfer list.
- `SUPPORT_NUMBER`: Dedicated support line for the transfer list.

### Step 2: Understand the Qualification Prompt

The qualification prompt is the core of your speed-to-lead agent. It tells the AI exactly how to handle the call. Here is the prompt used in the example code, broken down section by section:

```
You are a friendly, professional sales development representative
for {{company_name}}. You are calling {{lead_name}} who just
expressed interest in {{product_interest}} through {{lead_source}}.

Your goals on this call:
1. Greet them warmly by name and reference what they were looking at.
2. Confirm they are the right person and that now is a good time to talk.
3. Ask these qualifying questions naturally (do not read them like a list):
   - What problem are they trying to solve?
   - What is their timeline for making a decision?
   - Who else is involved in the decision?
   - Do they have a budget range in mind?
4. Based on their answers, determine if they are a qualified lead.
5. If they seem qualified and interested, offer to transfer them to
   a specialist right now, or offer to book a demo at a time that
   works for them.
6. If they are not qualified or not interested, thank them politely
   and let them know you will send a follow-up email with more
   information.

Important rules:
- Be conversational and natural. Do not sound like a robot.
- Do not ask all questions at once. Let the conversation flow.
- If they seem busy, offer to call back at a better time.
- Never be pushy or aggressive.
- If they ask a question you cannot answer, say you will have a
  specialist follow up with the answer.
```

**Key elements:**
- `{{lead_name}}`, `{{product_interest}}`, and `{{lead_source}}` are dynamic variables injected via `request_data`. Bland replaces these with the actual values at call time.
- The prompt asks qualifying questions (timeline, budget, decision maker) that map to standard BANT criteria (Budget, Authority, Need, Timeline).
- The agent can transfer hot leads immediately or book a follow-up demo.

### Step 3: Configure Voicemail Handling

Not every lead will answer the phone. When the call goes to voicemail, the agent should leave a personalized message instead of hanging up:

```json
{
  "action": "leave_message",
  "message": "Hi {{lead_name}}, this is Alex from {{company_name}}. You recently expressed interest in {{product_interest}} and I wanted to connect with you personally. I will send you a follow-up email with some helpful information. If you would like to chat, you can call us back at this number anytime. Looking forward to connecting with you!"
}
```

The `action` field supports three options:
- `"leave_message"`: The agent speaks the `message` text and then hangs up.
- `"hangup"`: The agent immediately hangs up without leaving a message.
- `"ignore"`: The agent continues talking as if someone answered (not recommended for lead calling).

### Step 4: Set Up Call Transfers

For hot leads who are ready to buy, you want to transfer them to a live sales rep immediately. The example code uses two transfer mechanisms:

**Single transfer number:**
```json
{
  "transfer_phone_number": "+15559876543"
}
```

**Transfer list (multiple departments):**
```json
{
  "transfer_list": {
    "default": "+15559876543",
    "sales": "+15559876543",
    "support": "+15551112222"
  }
}
```

With a transfer list, the AI agent decides which department to transfer to based on the conversation context. If the lead asks a sales question, the agent transfers to the `"sales"` number. If they have a support issue, it goes to `"support"`.

### Step 5: Run the Webhook Server

Start the webhook server to receive both lead form submissions and post-call results:

**Python:**
```bash
cd python
python webhook_receiver.py
# Server starts on port 5000
```

**Node.js:**
```bash
cd node
node webhookReceiver.js
# Server starts on port 3000
```

If testing locally, expose your server with ngrok:

```bash
# For Python (port 5000)
ngrok http 5000

# For Node.js (port 3000)
ngrok http 3000
```

Copy the ngrok HTTPS URL and update `WEBHOOK_URL` in your `.env` file to point to `https://your-ngrok-url.ngrok.io/webhook/call-complete`.

### Step 6: Submit a Test Lead

Send a test lead submission to your webhook server:

```bash
curl -X POST http://localhost:5000/webhook/lead-form \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "phone": "+15551234567",
    "email": "jane@example.com",
    "source": "Website Contact Form",
    "interest": "Enterprise Plan"
  }'
```

Within seconds, Bland AI will call the phone number. Answer the call and have a conversation with the AI agent. After the call ends, check your server logs to see the post-call webhook data arrive at `/webhook/call-complete`.

### Step 7: Process Post-Call Results

When a call finishes, Bland sends a POST request to your `WEBHOOK_URL` with the following data:

```json
{
  "call_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "completed",
  "answered_by": "human",
  "call_length": 3.45,
  "transcripts": [
    { "text": "Hi Jane, this is Alex from...", "user": "agent" },
    { "text": "Oh hi, yes I was just looking at...", "user": "user" }
  ],
  "concatenated_transcript": "Agent: Hi Jane... User: Oh hi...",
  "summary": "Called Jane Smith about Enterprise Plan interest...",
  "variables": {
    "qualified": true,
    "budget": "$50k-100k",
    "timeline": "Q2 2026",
    "transferred": true
  },
  "recording_url": "https://...",
  "price": 0.12
}
```

The example webhook receiver logs all of this data and includes placeholder code showing where you would push results to your CRM (Salesforce, HubSpot, Pipedrive, etc.).

## Integrating with Form Builders

### Typeform

In Typeform, go to Connect > Webhooks and add your server URL:
```
https://your-server.com/webhook/lead-form
```

Map your Typeform fields to the expected JSON format using a Typeform webhook or Zapier:
```json
{
  "name": "{{answer_for_name_field}}",
  "phone": "{{answer_for_phone_field}}",
  "email": "{{answer_for_email_field}}",
  "source": "Typeform",
  "interest": "{{answer_for_interest_field}}"
}
```

### HubSpot

Use HubSpot Workflows to trigger a webhook when a new contact is created or a form is submitted:

1. Go to Automation > Workflows in HubSpot.
2. Create a new workflow triggered by "Form submission."
3. Add a "Send webhook" action pointing to `https://your-server.com/webhook/lead-form`.
4. Map the contact properties to the expected JSON format.

### Zapier

1. Create a new Zap with your form builder as the trigger.
2. Add a "Webhooks by Zapier" action with the POST method.
3. Set the URL to `https://your-server.com/webhook/lead-form`.
4. Map the form fields to `name`, `phone`, `email`, `source`, and `interest`.

### Direct HTML Form

If you control the form, you can POST directly to your webhook server:

```html
<form id="lead-form">
  <input type="text" name="name" placeholder="Your name" required />
  <input type="tel" name="phone" placeholder="+15551234567" required />
  <input type="email" name="email" placeholder="you@example.com" required />
  <input type="hidden" name="source" value="Website Contact Form" />
  <select name="interest">
    <option value="Starter Plan">Starter Plan</option>
    <option value="Pro Plan">Pro Plan</option>
    <option value="Enterprise Plan">Enterprise Plan</option>
  </select>
  <button type="submit">Get a Call Back</button>
</form>

<script>
  document.getElementById("lead-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    await fetch("https://your-server.com/webhook/lead-form", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    alert("Thanks! You will receive a call shortly.");
  });
</script>
```

## API Reference

### Send Call

**Endpoint:** `POST https://api.bland.ai/v1/calls`

**Headers:**

| Header          | Value              | Description                    |
| --------------- | ------------------ | ------------------------------ |
| `Authorization` | `YOUR_API_KEY`     | Your Bland API key (no prefix) |
| `Content-Type`  | `application/json` | Required for JSON body         |

**Parameters Used in This Cookbook:**

| Parameter               | Type    | Description                                                                                          |
| ----------------------- | ------- | ---------------------------------------------------------------------------------------------------- |
| `phone_number`          | string  | The lead's phone number in E.164 format (e.g., `+15551234567`).                                     |
| `task`                  | string  | The qualification prompt that defines agent behavior.                                                |
| `first_sentence`        | string  | Personalized greeting using the lead's name.                                                         |
| `voice`                 | string  | The voice the agent uses (e.g., `"mason"`, `"maya"`).                                                |
| `model`                 | string  | The model to use. `"base"` is recommended for qualification calls.                                   |
| `max_duration`          | integer | Maximum call length in minutes. 10 minutes is ideal for qualification calls.                         |
| `record`                | boolean | Set to `true` to record the call for review.                                                         |
| `request_data`          | object  | Dynamic variables injected into the prompt (lead name, email, source, interest).                     |
| `webhook`               | string  | URL that receives a POST with full call data when the call completes.                                |
| `transfer_phone_number` | string  | Default number for transferring qualified leads.                                                     |
| `transfer_list`         | object  | Multiple transfer targets keyed by department name.                                                  |
| `voicemail`             | object  | Controls voicemail behavior. See voicemail handling section above.                                    |
| `tools`                 | array   | Custom tools the agent can use during the call (e.g., a booking tool).                               |

**Success Response:**

```json
{
  "status": "success",
  "message": "Call successfully queued.",
  "call_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

## Verifying It Works

1. Start your webhook server (Python on port 5000, Node.js on port 3000).
2. If testing locally, start ngrok and update `WEBHOOK_URL` in `.env`.
3. Submit a test lead using curl or your form.
4. Your phone should ring within 5 to 10 seconds.
5. Answer the call and talk to the AI agent. It will greet you by name and ask qualifying questions.
6. After the call ends, check your server logs for the post-call webhook data at `/webhook/call-complete`.
7. Verify the transcript, summary, and extracted variables are present.

## Troubleshooting

### "Authorization header is missing or invalid"

Your API key is not being sent correctly. Double check that:
- Your `.env` file contains the correct key with no extra spaces or quotes.
- The key starts with the expected prefix (usually `sk-`).
- The `.env` file is in the same directory as the script you are running.

### The call is queued but my phone never rings

A few things to check:
- Confirm the phone number is correct and in E.164 format (e.g., `+15551234567`).
- Make sure your Bland account has sufficient credits.
- Check the Bland dashboard under the Calls tab for error details.

### The webhook never fires

- Make sure your `WEBHOOK_URL` is publicly accessible. Bland cannot reach `localhost`.
- Use ngrok for local testing: `ngrok http 5000` (or `3000` for Node.js).
- Verify the URL has no trailing slashes or typos.
- Check the Bland dashboard for the call's webhook delivery status.

### The agent does not transfer the call

- Verify `TRANSFER_NUMBER` is set correctly in your `.env` file.
- The transfer only happens if the AI determines the lead is qualified. Try being enthusiastic and expressing urgency during the test call.

### Voicemail message is not left

- Make sure the `voicemail` parameter is included in the call payload.
- The `action` must be `"leave_message"` (not `"hangup"` or `"ignore"`).

## Next Steps

Now that you have a working speed-to-lead system, consider these enhancements:

- **Add a booking tool.** Give the agent the ability to check calendar availability and book meetings directly during the call using Bland's custom tools feature. See the Custom Tools cookbook for details.
- **Score leads automatically.** Use the post-call `variables` to assign a lead score and route high-priority leads differently.
- **Set up retries.** If a call goes to voicemail, automatically schedule a follow-up call 30 minutes later using the Batch Campaigns cookbook.
- **Connect to your CRM.** Replace the placeholder CRM code in the webhook receiver with real API calls to Salesforce, HubSpot, or Pipedrive.
- **Add SMS follow-up.** After a voicemail, send an SMS with a link to book a meeting. See the SMS Messaging cookbook for details.
- **Track metrics.** Log call outcomes (qualified, not qualified, voicemail, no answer) and build a dashboard to monitor your speed-to-lead performance.

Check out the other cookbooks in this series for more advanced use cases like batch campaigns, appointment scheduling, and call analysis.
