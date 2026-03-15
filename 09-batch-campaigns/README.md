# 09 - Batch Campaigns

This cookbook shows you how to run large-scale outbound calling campaigns using the Bland AI Batch API. Instead of sending calls one at a time, you can submit hundreds or thousands of calls in a single request, each personalized with data from a CSV file.

## What You Will Build

A complete batch campaign system that:

1. Reads a CSV of patient records and builds personalized call objects
2. Submits them as a single batch to the Bland API
3. Monitors the batch in real time, displaying progress as calls complete
4. Can stop a running batch if needed

The example scenario is a dental office calling 100 patients to remind them of upcoming appointments. Each call is personalized with the patient's name, appointment date, time, dentist name, and service type.

## What Are Batch Campaigns?

Batch campaigns let you send many outbound calls at once through a single API request. Rather than looping through a list and calling `POST /v1/calls` for each contact, you submit the entire list to `POST /v1/batches`. Bland handles the queuing, dispatching, retries, and lifecycle tracking for you.

Each call in the batch can be individually customized (different phone number, different variables, different scheduling), while a shared "global" configuration provides sensible defaults for the entire batch.

### Common Use Cases

- **Appointment reminders.** Notify patients, clients, or customers about upcoming appointments with personalized details.
- **Sales outreach.** Call a list of leads with tailored pitches based on their industry, company size, or previous interactions.
- **Surveys and feedback.** Collect post-purchase or post-visit feedback from a customer list.
- **Collections and billing.** Remind customers about overdue invoices or upcoming payment deadlines.
- **Event notifications.** Inform attendees about event details, schedule changes, or cancellations.
- **Re-engagement campaigns.** Reach out to inactive customers with special offers or check-ins.

## Prerequisites

Before you begin, make sure you have:

- **A Bland AI account.** Sign up at [app.bland.ai](https://app.bland.ai) if you do not have one.
- **An API key.** Find yours in the Bland dashboard under Settings > API Keys.
- **Sufficient account credits.** Batch campaigns can consume credits quickly. Start with a small test batch before scaling up.

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
# Edit .env and add your API key

# Create a batch campaign from the sample CSV
python create_batch.py

# Monitor the batch (use the batch_id printed by the previous command)
python monitor_batch.py <batch_id>

# Stop a batch if needed
python stop_batch.py <batch_id>
```

### Node.js

```bash
cd node
npm install axios dotenv
cp .env.example .env
# Edit .env and add your API key

# Create a batch campaign from the sample CSV
node createBatch.js

# Monitor the batch (use the batch_id printed by the previous command)
node monitorBatch.js <batch_id>

# Stop a batch if needed
node stopBatch.js <batch_id>
```

## Step-by-Step Guide

### Step 1: Prepare Your CSV

The foundation of a batch campaign is your contact list. Create a CSV file where each row represents one call. The column names become dynamic variables that you can reference in your prompt using `{{column_name}}` syntax.

**Rules for CSV files:**

- You must include a `phone_number` column. This is the only required column.
- Column names cannot contain spaces. Use underscores instead (e.g., `patient_name`, not `patient name`).
- Phone numbers should be in E.164 format (e.g., `+15551234567`).
- Every other column becomes a variable you can use in your prompt template.

Here is an example row from the included `sample_leads.csv`:

```
phone_number,patient_name,appointment_date,appointment_time,dentist_name,service_type
+15551234567,Sarah Johnson,March 15 2026,10:00 AM,Dr. Williams,Routine Cleaning
```

In your prompt, you would reference these as `{{patient_name}}`, `{{appointment_date}}`, `{{appointment_time}}`, `{{dentist_name}}`, and `{{service_type}}`.

### Step 2: Understand Global Config vs Per-Call Overrides

The batch API uses a two-layer configuration system:

**Global config** applies to every call in the batch. This is where you put settings that are the same across all calls, such as the prompt template, voice, model, and recording preferences. The global config must include either a `task` (prompt) or a `pathway_id`. It cannot include `phone_number`, since that is unique to each call.

**Per-call overrides** (the `call_objects` array) let you customize individual calls. Each entry must have a `phone_number`. Any other parameter you include will override the global default for that specific call. For example, you could set a Spanish-language override for certain contacts or assign different voices to different calls.

```
Global config (shared defaults)
  +-- Call 1: phone_number + any overrides
  +-- Call 2: phone_number + any overrides
  +-- Call 3: phone_number only (uses all global defaults)
  +-- ...
```

### Step 3: Create the Batch

Run `create_batch.py` or `createBatch.js`. The script reads the CSV, builds a `call_objects` array with one entry per row, attaches the global configuration, and submits everything to `POST /v1/batches`.

The API responds immediately with a `batch_id`. The calls do not start instantly. Bland validates the batch first, then begins dispatching calls. You can track this process through polling or webhooks.

### Step 4: Monitor the Batch

Use `monitor_batch.py` or `monitorBatch.js` with the `batch_id` to watch your campaign in real time. The script polls `GET /v1/batches/{batch_id}` every 10 seconds and displays the current status, number of completed calls, in-progress calls, and failed calls.

### Step 5: Analyze Results

Once the batch completes, you can retrieve individual call details using `GET /v1/calls/{call_id}` for each call in the batch. This gives you transcripts, summaries, recordings, and any variables that were extracted during the conversation.

## Dynamic Variables from CSV Columns

When you include columns beyond `phone_number` in your CSV, those values become available as template variables in your prompt. The substitution happens automatically when Bland dispatches each call.

For example, with this CSV row:

```
+15551234567,Sarah Johnson,March 15 2026,10:00 AM
```

And this prompt template:

```
You are calling {{patient_name}} to remind them about their appointment on {{appointment_date}} at {{appointment_time}}.
```

The actual prompt for that call becomes:

```
You are calling Sarah Johnson to remind them about their appointment on March 15 2026 at 10:00 AM.
```

This is the same mechanism as `request_data` in the single-call API. In the batch context, the CSV columns populate the `request_data` for each call automatically.

## Scheduling Calls with start_time

You can schedule individual calls within a batch to start at specific times. This is useful when you want to respect time zones, avoid calling too early or too late, or spread calls across a time window.

Set `start_time` in each call object as an ISO 8601 datetime string:

```json
{
  "phone_number": "+15551234567",
  "start_time": "2026-03-15T09:00:00-05:00"
}
```

You can mix scheduled and immediate calls in the same batch. Calls without a `start_time` will be dispatched as soon as the batch begins processing.

When a batch contains scheduled calls, you may see the status `waiting_for_scheduled_calls` after the immediate calls finish but before all scheduled calls have been dispatched.

## Status Webhook Integration

Instead of polling, you can receive real-time updates about your batch by providing a `status_webhook` URL. Bland will send POST requests to this URL as the batch progresses through its lifecycle.

### Batch Lifecycle Statuses

| Status | Description |
| --- | --- |
| `validating` | Bland is validating the batch configuration and call objects |
| `dispatching` | Calls are being queued and sent out |
| `in_progress` | Calls are actively running |
| `in_progress_chunked` | Large batch is being processed in chunks |
| `waiting_for_scheduled_calls` | Immediate calls are done, waiting for scheduled calls to dispatch |
| `completed` | All calls have finished successfully |
| `completed_partial` | The batch finished but some calls failed |
| `failed` | The batch failed to process |

### Webhook Payload

Each status update sends a JSON payload:

```json
{
  "batch_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "in_progress",
  "timestamp": "2026-03-15T14:30:00Z"
}
```

When the batch reaches a terminal status (`completed`, `completed_partial`, or `failed`), the payload includes additional summary fields:

```json
{
  "batch_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "completed",
  "timestamp": "2026-03-15T15:00:00Z",
  "calls_total": 100,
  "calls_successful": 97,
  "calls_failed": 3
}
```

## API Reference

### Create Batch

**Endpoint:** `POST https://api.bland.ai/v1/batches`

**Headers:**

| Header | Value | Description |
| --- | --- | --- |
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |
| `Content-Type` | `application/json` | Required for JSON body |

**Body Parameters:**

| Parameter | Type | Required | Description |
| --- | --- | --- | --- |
| `call_objects` | array | Yes | Array of individual call entries. Each must have `phone_number`. Can include any parameter from `/v1/calls`. |
| `global` | object | Yes | Default properties applied to all calls. Must include `task` or `pathway_id`. Cannot include `phone_number`. |
| `status_webhook` | string | No | URL that receives POST requests with batch lifecycle updates. |

**Success Response:**

```json
{
  "data": {
    "batch_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  },
  "errors": null
}
```

### Get Batch

**Endpoint:** `GET https://api.bland.ai/v1/batches/{batch_id}`

**Headers:**

| Header | Value | Description |
| --- | --- | --- |
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |

Returns the batch details including status, call counts, and metadata.

### List All Batches

**Endpoint:** `GET https://api.bland.ai/v1/batches`

**Headers:**

| Header | Value | Description |
| --- | --- | --- |
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |

Returns all batches associated with your account.

### Stop Batch

**Endpoint:** `POST https://api.bland.ai/v1/batches/{batch_id}/stop`

**Headers:**

| Header | Value | Description |
| --- | --- | --- |
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |

Stops a running batch. Calls that are already in progress will complete, but no new calls will be dispatched.

## How to Verify

Before running a full campaign, always test with a small batch:

1. **Edit `sample_leads.csv`** and replace the phone numbers with your own phone number. Use just 1 to 3 rows for testing.
2. **Run the create script.** You should receive a `batch_id` in the response.
3. **Answer the call** when your phone rings. Verify that the agent uses the correct patient name, appointment date, and other personalized details from your CSV.
4. **Run the monitor script** with the `batch_id` to confirm you can track progress.
5. **Check the Bland dashboard** at [app.bland.ai](https://app.bland.ai) under the Calls tab to review transcripts and recordings.

Once you are confident everything works, swap in your real CSV and run the full campaign.

## Best Practices for Large Campaigns

### Start Small, Scale Gradually

Run a test batch of 5 to 10 calls before launching hundreds. Verify your prompt sounds natural, the variables are substituting correctly, and the agent handles common responses well.

### Use Descriptive Column Names

Choose CSV column names that clearly describe the data: `appointment_date` is better than `date`, and `dentist_name` is better than `name`. This makes your prompt template more readable and reduces confusion.

### Set Reasonable Max Durations

For short, transactional calls like appointment reminders, set `max_duration` to 3 to 5 minutes. This prevents runaway calls and keeps costs predictable.

### Handle Voicemail Gracefully

Configure the `voicemail` setting in your global config. For reminder campaigns, leaving a brief voicemail message is usually better than hanging up silently.

### Respect Time Zones

If your contacts span multiple time zones, use `start_time` to schedule calls during appropriate hours. Avoid calling before 9:00 AM or after 8:00 PM in the recipient's local time.

### Use the Status Webhook in Production

Polling works for development and testing, but in production you should use the `status_webhook` to receive push notifications. This is more efficient and gives you immediate awareness when something goes wrong.

### Monitor Failure Rates

After a batch completes, check the ratio of successful to failed calls. A high failure rate might indicate invalid phone numbers, insufficient credits, or a problem with your prompt that causes the agent to behave unexpectedly.

### Record Calls for Quality Assurance

Enable recording on at least a sample of your calls. Listen to a few recordings after each campaign to identify areas where the agent's prompt could be improved.

### Keep Prompts Concise on the Phone

Phone conversations are different from chat. Keep agent responses to one or two sentences at a time. Long monologues cause people to hang up or zone out.

### Plan for Callbacks

Some recipients will want to call back. Consider setting up an inbound agent (see cookbook 02) that can handle return calls and answer follow-up questions about their appointment.

## Troubleshooting

### "Authorization header is missing or invalid"

Your API key is not being sent correctly. Double check that:
- Your `.env` file contains the correct key with no extra spaces or quotes.
- The key starts with the expected prefix (usually `sk-`).
- The `.env` file is in the same directory as the script you are running.

### "Invalid phone number" errors in the batch

One or more phone numbers in your CSV are not in valid E.164 format. Check that:
- Every number starts with `+` followed by the country code.
- US numbers look like `+15551234567` (11 digits total with the `+1` country code).
- No spaces, dashes, or parentheses in the numbers.
- There are no empty rows or missing values in the `phone_number` column.

### Batch status is "failed"

The entire batch failed validation. Common causes:
- The `global` config is missing both `task` and `pathway_id`.
- The `global` config incorrectly includes a `phone_number`.
- The `call_objects` array is empty.

### Some calls show as failed but the batch completed

This is the `completed_partial` status. Individual calls can fail for reasons such as:
- Invalid or disconnected phone numbers.
- The recipient's carrier blocking the call.
- Network issues during the call.

Check the individual call details using `GET /v1/calls/{call_id}` and review the `error_message` field.

### The monitor script shows no progress

Make sure you are using the correct `batch_id`. Also check that your account has sufficient credits. If the batch is stuck in `validating`, there may be an issue with your batch configuration.

## Next Steps

Now that you can run batch campaigns, explore these ideas:

- **Add webhook handling.** Build a server endpoint that receives batch status updates and call completion data in real time.
- **Integrate with your CRM.** Pull contact lists from your CRM instead of a static CSV file, and push call results back after each campaign.
- **Use pathways instead of task prompts.** For complex, multi-step conversations, set `pathway_id` in the global config instead of `task`.
- **Implement retry logic.** For failed calls, extract the failed phone numbers and create a follow-up batch.
- **Schedule across time zones.** Use the `start_time` parameter to dispatch calls at appropriate local times for each recipient.

Check out the other cookbooks in this series for more advanced features like inbound call handling, pathway-based agents, and call analysis.
