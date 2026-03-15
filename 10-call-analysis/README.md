# Cookbook 10: Call Analysis

Extract insights from every phone call. This cookbook covers four approaches for getting call data out of Bland AI: polling the calls API, running AI-powered analysis on transcripts, using citation schemas for structured extraction with source tracing, and receiving real-time webhook notifications. You will build scripts that list recent calls, analyze them with custom questions, extract structured data with citations, auto-schedule follow-ups, and listen for post-call webhooks.

## Why Call Analysis Matters

Every call your AI agent handles generates valuable data: transcripts, summaries, durations, outcomes, and more. The challenge is turning that raw data into actionable insights. Did the customer express interest? Was the issue resolved? How satisfied did they seem?

Bland AI gives you four complementary approaches:

1. **Polling the Calls API.** Fetch call details on demand. Good for dashboards, one-off lookups, and backfilling historical data.
2. **AI Analysis Endpoint.** Ask natural-language questions about any call and get structured answers (booleans, numbers, strings). Perfect for scoring calls, extracting key facts, and building automated QA pipelines.
3. **Citation Schemas.** Define structured fields to extract from every call. Each extracted value is linked back to the exact utterance in the transcript where it was mentioned, making the data auditable. Use citations to auto-schedule follow-ups, update CRMs, and trigger workflows.
4. **Post-Call Webhooks.** Receive call data the moment a call ends, with no polling required. Ideal for real-time pipelines, CRM updates, and alerting.

## What You Will Build

Four scripts (in both Python and Node.js):

| Script | Purpose |
|--------|---------|
| `list_calls` / `listCalls` | Fetch recent calls and display them in a formatted table |
| `analyze_call` / `analyzeCall` | Fetch a single call's details, then run AI analysis with custom questions |
| `call_with_citations` / `callWithCitations` | Send a call with citation schemas, extract structured data with source tracing, and auto-schedule follow-ups with SMS confirmation |
| `webhook_listener` / `webhookListener` | A local server that receives and processes post-call webhook payloads |

## Prerequisites

- A Bland AI account with at least one completed call ([app.bland.ai](https://app.bland.ai))
- Your API key from Settings > API Keys

### Python

```bash
pip install requests python-dotenv flask
```

### Node.js

```bash
npm init -y
npm install axios dotenv express
```

## Quick Start

### Python

```bash
cd python
cp .env.example .env
# Edit .env and add your API key
pip install requests python-dotenv flask

# List your recent calls
python list_calls.py

# Analyze a specific call (pass a call_id, or omit to use the most recent call)
python analyze_call.py <call_id>

# Send a call with citations and auto-schedule a follow-up
python call_with_citations.py

# Start the webhook listener on port 3000
python webhook_listener.py
```

### Node.js

```bash
cd node
cp .env.example .env
# Edit .env and add your API key
npm install axios dotenv express

# List your recent calls
node listCalls.js

# Analyze a specific call (pass a call_id, or omit to use the most recent call)
node analyzeCall.js <call_id>

# Send a call with citations and auto-schedule a follow-up
node callWithCitations.js

# Start the webhook listener on port 3000
node webhookListener.js
```

## The Three Approaches in Detail

### Approach 1: Polling the Calls API

The simplest way to get call data. Make a GET request to list all calls or fetch a single call by its ID.

**List all calls:**

```
GET https://api.bland.ai/v1/calls
Authorization: YOUR_API_KEY
```

Returns an array of call objects with full details for each call.

**Get a single call:**

```
GET https://api.bland.ai/v1/calls/{call_id}
Authorization: YOUR_API_KEY
```

Returns the complete call object. Here is every field you can expect:

| Field | Type | Description |
|-------|------|-------------|
| `call_id` | string | Unique identifier for the call |
| `c_id` | string | Alternate compact identifier |
| `batch_id` | string | If this call was part of a batch, the batch identifier |
| `pathway_id` | string | If this call used a pathway, the pathway identifier |
| `call_length` | float | Duration of the call in minutes |
| `corrected_duration` | float | Duration adjusted for any post-processing corrections |
| `to` | string | The phone number that was called |
| `from` | string | The phone number the call originated from |
| `inbound` | boolean | Whether this was an inbound call (true) or outbound (false) |
| `answered_by` | string | Whether the call was answered by a "human" or "voicemail" |
| `queue_status` | string | The queue status (e.g., "complete", "queued") |
| `status` | string | Current status (e.g., "completed", "in-progress") |
| `completed` | boolean | Whether the call has finished |
| `call_ended_by` | string | Who ended the call: "agent", "user", or "system" |
| `transcripts` | array | Array of transcript entries, each with `id`, `created_at`, `text`, and `user` (speaker type) |
| `concatenated_transcript` | string | The full transcript as a single string with speaker labels |
| `summary` | string | AI-generated summary of the call |
| `price` | float | Cost of the call in USD |
| `recording_url` | string | URL to the call recording (only if `record` was true) |
| `record` | boolean | Whether recording was enabled |
| `variables` | object | Any variables extracted or set during the call |
| `analysis_schema` | object | The analysis schema if one was configured on the call |
| `analysis` | object | Results from any pre-configured analysis |
| `pathway_logs` | array | Detailed logs if the call used a pathway |
| `error_message` | string | Error details if the call failed, otherwise null |
| `request_data` | object | The custom data that was passed when the call was created |
| `metadata` | object | Any metadata attached to the call |

**When to use polling:**

- Building a dashboard that refreshes periodically
- Running one-off investigations on specific calls
- Backfilling historical data into your analytics database
- Simple scripts where real-time updates are not needed

### Approach 2: AI Analysis Endpoint

Ask natural-language questions about any completed call and get structured, typed answers. This is powerful for automated QA, lead scoring, compliance checks, and extracting specific facts from conversations.

**Endpoint:**

```
POST https://api.bland.ai/v1/calls/{call_id}/analyze
Authorization: YOUR_API_KEY
Content-Type: application/json
```

**Request body:**

```json
{
  "goal": "Evaluate how well the sales call went and whether the customer is interested.",
  "questions": [
    ["Did the customer express interest in the product?", "boolean"],
    ["What was the customer's main concern?", "string"],
    ["Was the issue resolved?", "boolean"],
    ["On a scale of 1 to 10, how satisfied did the customer seem?", "number"],
    ["Was the call answered by a human or voicemail?", "human or voicemail"]
  ]
}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `goal` | string | Overall purpose and context for the analysis. Helps the AI understand what you care about. |
| `questions` | array | An array of question pairs. Each pair is a two-element array: `[question_text, answer_type]`. |

**Answer types:**

| Type | What it returns | Example |
|------|----------------|---------|
| `"string"` | A free-text answer | "The customer was concerned about pricing and delivery timeline." |
| `"boolean"` | true or false | true |
| `"number"` | A numeric value | 7 |
| Custom string | One of the values you specify | "human" (from type "human or voicemail") |

If a question cannot be answered from the transcript, the answer will be `null`.

**Response:**

```json
{
  "status": "success",
  "answers": [true, "Pricing was too high for their budget.", false, 5, "human"],
  "credits_used": 0.003
}
```

**Pricing:** Base cost is 0.003 credits per analysis request, plus 0.0015 per call. The total is adjusted based on transcript length.

**When to use the analysis endpoint:**

- Scoring leads after sales calls
- Automated QA and compliance checks
- Extracting structured data from unstructured conversations
- Building reports that summarize trends across many calls

### Approach 3: Citation Schemas (Structured Extraction with Source Tracing)

Citation schemas take analysis a step further. Instead of asking questions after the call, you define the exact fields you want extracted up front. Bland's AI reads the transcript and populates each field automatically. The key differentiator: every extracted value is paired with a **citation** that points to the exact utterance in the transcript where the information came from.

This makes your post-call data auditable. If your system records that a customer's email is `alex@example.com`, you can trace that back to the exact moment in the conversation where they said it.

**Two ways to use citation schemas:**

1. **Inline with `analysis_schema`:** Define fields directly on each call. Good for prototyping and one-off use cases.
2. **Pre-created with `citation_schema_ids`:** Create reusable schemas in the Bland dashboard (or via the API) and reference them by ID. Better for production where you want consistent extraction across all calls.

**Using analysis_schema (inline):**

```json
{
  "phone_number": "+15551234567",
  "task": "Your agent prompt here...",
  "analysis_schema": {
    "customer_name": "The customer's full name.",
    "customer_email": "The customer's email address.",
    "wants_follow_up": "Did the customer agree to a follow-up? true or false.",
    "preferred_follow_up_time": "When they want the follow-up. Null if declined.",
    "customer_sentiment": "Overall sentiment: positive, neutral, or negative."
  }
}
```

**Using citation_schema_ids (pre-created):**

```json
{
  "phone_number": "+15551234567",
  "task": "Your agent prompt here...",
  "citation_schema_ids": ["schema-uuid-from-dashboard"]
}
```

Both approaches produce the same output. After the call, the call details include:

**The `analysis` object** contains the extracted values:

```json
{
  "analysis": {
    "customer_name": "Alex Johnson",
    "customer_email": "alex@example.com",
    "wants_follow_up": true,
    "preferred_follow_up_time": "Tuesday at 2 PM",
    "customer_sentiment": "positive"
  }
}
```

**The `citations` array** links each value to its source:

```json
{
  "citations": [
    {
      "field": "customer_email",
      "value": "alex@example.com",
      "utterance": "Sure, my email is alex@example.com.",
      "speaker": "user",
      "confidence": 0.95
    },
    {
      "field": "wants_follow_up",
      "value": true,
      "utterance": "Yes, I would love to schedule a demo next week.",
      "speaker": "user",
      "confidence": 0.92
    }
  ]
}
```

Each citation includes:

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | The schema field name this citation relates to |
| `value` | any | The extracted value |
| `utterance` | string | The exact text from the transcript where this was mentioned |
| `speaker` | string | Who said it: `"user"` (the customer) or `"agent"` (the AI) |
| `confidence` | float | How confident the AI is in this extraction (0 to 1) |

**When to use citation schemas:**

- Extracting structured data (names, emails, dates, preferences) from every call
- Building automated follow-up workflows based on call outcomes
- CRM updates where you need auditable data provenance
- Compliance scenarios where you must prove where information came from

**Auto-scheduling follow-ups with citations:**

The `call_with_citations` script in this cookbook demonstrates the full workflow:

1. Send a call with an analysis_schema that includes follow-up fields.
2. After the call, read the extracted data to check if the customer wants a follow-up.
3. If yes, automatically create a follow-up call using the extracted preferred time.
4. Optionally send an SMS confirmation to the customer.

This turns a manual process (listen to recording, take notes, schedule follow-up) into a fully automated pipeline.

### Approach 4: Post-Call Webhooks

Receive call data automatically the moment a call completes. No polling, no delays (beyond network latency). Set the `webhook` parameter when creating a call, and Bland will POST the results to your URL.

**Setting up a webhook when creating a call:**

```json
{
  "phone_number": "+15551234567",
  "task": "Your agent prompt here...",
  "webhook": "https://your-server.com/webhook/call-complete"
}
```

**Immediate webhook payload fields:**

| Field | Type | Description |
|-------|------|-------------|
| `call_id` | string | The unique call identifier |
| `c_id` | string | Alternate compact identifier |
| `call_length` | float | Duration in minutes |
| `completed` | boolean | Whether the call finished |
| `inbound` | boolean | Whether this was an inbound call |
| `error_message` | string | Error details, or null |
| `summary` | string | AI-generated summary |
| `price` | float | Cost of the call in USD |
| `recording_url` | string | Recording URL if enabled |
| `transcripts` | array | Array of transcript entries |
| `concatenated_transcript` | string | Full transcript with speaker labels |
| `pathway_logs` | array | Pathway execution logs if applicable |
| `variables` | object | Extracted or set variables |
| `metadata` | object | Custom metadata |
| `call_ended_by` | string | Who ended the call |
| `disposition_tag` | string | The disposition label selected by the agent |
| `transferred_to` | string | Number the call was transferred to, if any |
| `pre_transfer_duration` | float | Duration before transfer |
| `post_transfer_duration` | float | Duration after transfer |

**Delayed webhook payload (arrives 30 to 60 seconds later):**

A second webhook fires with additional processed data:

| Field | Type | Description |
|-------|------|-------------|
| `corrected_transcript` | object | Enhanced transcript with speaker labels and confidence scores |
| `citations` | array | Links specific variables to the utterances where they were mentioned |

### Webhook Events (Streaming)

For even more granular tracking, use the `webhook_events` parameter when creating a call. This sends separate webhook POSTs for each event type as they happen during the call:

```json
{
  "phone_number": "+15551234567",
  "task": "Your agent prompt here...",
  "webhook": "https://your-server.com/webhook/events",
  "webhook_events": ["queue", "call", "latency", "webhook", "tool", "dynamic_data", "citations"]
}
```

| Event | When it fires |
|-------|---------------|
| `queue` | When the call enters or leaves the queue |
| `call` | When the call connects or ends |
| `latency` | Latency measurements during the call |
| `webhook` | When a mid-call webhook fires (e.g., from a custom tool) |
| `tool` | When a tool is invoked during the call |
| `dynamic_data` | When dynamic data is fetched during the call |
| `citations` | When corrected transcript and citations are ready (post-call) |

### Using Dispositions for Categorization

Dispositions let you define a set of outcome labels for your calls. The AI agent automatically selects the most appropriate one at the end of each call.

```json
{
  "phone_number": "+15551234567",
  "task": "Your sales agent prompt...",
  "dispositions": ["Interested", "Not Interested", "Callback Requested", "Wrong Number", "Voicemail"]
}
```

The selected disposition appears in the webhook payload as `disposition_tag` and in the call details via the API. Dispositions are useful for:

- Routing follow-up actions based on outcome
- Building disposition reports across batches
- Filtering calls by outcome in your analytics

### Custom Summary Prompts

By default, Bland generates a summary of every call. You can customize the summary format and focus with the `summary_prompt` parameter:

```json
{
  "phone_number": "+15551234567",
  "task": "Your agent prompt...",
  "summary_prompt": "Summarize this call in three bullet points: (1) the customer's request, (2) what the agent offered, (3) the outcome and any follow-up actions needed."
}
```

This is helpful when you need summaries in a specific format for your CRM, ticketing system, or analytics pipeline.

### Working with Transcripts

Bland provides transcripts in two formats:

**Structured transcripts** (`transcripts` array):

```json
[
  {
    "id": 1,
    "created_at": "2024-01-15T10:30:00.000Z",
    "text": "Hi, thank you for calling. How can I help you today?",
    "user": "agent"
  },
  {
    "id": 2,
    "created_at": "2024-01-15T10:30:05.000Z",
    "text": "I am calling about my recent order.",
    "user": "user"
  }
]
```

Each entry includes:
- `id`: Sequential identifier for the utterance
- `created_at`: Timestamp of when the utterance occurred
- `text`: What was said
- `user`: Speaker type, either `"agent"` or `"user"`

**Concatenated transcript** (`concatenated_transcript` string):

```
Agent: Hi, thank you for calling. How can I help you today?
User: I am calling about my recent order.
```

A single string with speaker labels. Easier to read and display, but less useful for programmatic processing.

**Corrected transcript** (from delayed webhook):

```json
{
  "corrected_transcript": {
    "segments": [
      {
        "speaker": "agent",
        "text": "Hi, thank you for calling. How can I help you today?",
        "confidence": 0.97,
        "start_time": 0.5,
        "end_time": 3.2
      }
    ]
  }
}
```

The corrected transcript includes confidence scores and precise timestamps. This arrives 30 to 60 seconds after the call ends via a second webhook POST.

## Verifying Each Approach

### Verify polling

Run `list_calls.py` (or `listCalls.js`). You should see a table of your recent calls with IDs, phone numbers, durations, and truncated summaries. If you have no calls yet, send one first using the getting-started cookbook.

### Verify AI analysis

Run `analyze_call.py <call_id>` with a real call ID from your account. You should see the call details printed first, followed by answers to each analysis question. If you omit the call_id argument, the script will fetch your most recent call and analyze that.

### Verify webhooks

1. Start the webhook listener: `python webhook_listener.py` (or `node webhookListener.js`).
2. Expose your local server to the internet using a tool like [ngrok](https://ngrok.com): `ngrok http 3000`.
3. Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`).
4. Send a call with `webhook` set to `https://abc123.ngrok.io/webhook/call-complete`.
5. When the call ends, you should see the payload logged in your terminal.

## Best Practices for Production Analytics Pipelines

1. **Use webhooks as your primary data source.** Polling works for testing, but webhooks give you data the moment a call ends with no wasted API calls.

2. **Store raw payloads.** Save the complete webhook payload to your database before processing it. This lets you reprocess data later if your analysis logic changes.

3. **Run AI analysis asynchronously.** The `/analyze` endpoint costs credits and adds latency. Queue analysis jobs and process them in the background rather than blocking your webhook handler.

4. **Use dispositions for quick categorization.** Dispositions are free (included in the call cost) and give you an instant outcome label without needing a separate analysis call.

5. **Combine approaches.** Use webhooks for real-time ingestion, dispositions for quick tagging, and the analysis endpoint for deeper investigation on calls that need it.

6. **Set custom summary prompts.** Tailor summaries to your use case so they are immediately useful without further processing.

7. **Handle the delayed webhook.** The corrected transcript arrives 30 to 60 seconds after the immediate webhook. Design your system to merge these two payloads using the `call_id` as the key.

8. **Monitor for errors.** Check the `error_message` field in every call. Build alerts for non-null error messages so you can catch issues early.

9. **Paginate when listing calls.** If you have thousands of calls, use pagination parameters to avoid loading everything at once.

10. **Secure your webhook endpoint.** In production, validate incoming webhooks to ensure they come from Bland AI. Check the source IP or use a shared secret in the URL path.

## Troubleshooting

### "Authorization header is missing or invalid"

Double check that your `.env` file contains the correct API key with no extra spaces or quotes. The key typically starts with `sk-`.

### AI analysis returns null for all answers

This usually means the call has no transcript. The call may not have been answered, or it may have ended before any conversation took place. Check the `concatenated_transcript` field in the call details.

### Webhook never fires

Make sure the `webhook` URL is publicly accessible. Localhost URLs will not work unless you use a tunneling tool like ngrok. Also verify that the URL includes the full path (e.g., `https://your-server.com/webhook/call-complete`, not just `https://your-server.com`).

### "Module not found" errors

Install the dependencies for your language:
- Python: `pip install requests python-dotenv flask`
- Node.js: `npm install axios dotenv express`

### The list calls endpoint returns an empty array

You have no calls on your account yet. Send a test call using the getting-started cookbook first.

## Next Steps

- **Build a dashboard.** Combine the list calls and analysis endpoints to create a call analytics dashboard.
- **Set up automated QA.** Use webhooks plus the analysis endpoint to score every call automatically.
- **Integrate with your CRM.** Push call summaries, dispositions, and extracted variables into Salesforce, HubSpot, or your CRM of choice.
- **Track trends over time.** Store analysis results in a database and build reports showing how key metrics change week over week.

Check out the other cookbooks in this series for more advanced use cases including batch campaigns, pathway-based agents, and custom tool integrations.
