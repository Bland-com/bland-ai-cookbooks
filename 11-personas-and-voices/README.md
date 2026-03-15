# 11 - Personas and Voices

This cookbook covers Bland AI's persona system and voice catalog. You will learn how to browse available voices, create reusable personas that bundle your agent's personality, voice, and behavior into a single configuration, and then use those personas to send calls.

## What You Will Build

Three scripts (in both Python and Node.js) that:

1. **List Voices.** Fetch the full voice catalog from the Bland API, display them in a readable table, and filter for Bland Curated voices recommended for phone quality.
2. **Create a Persona.** Build a professional customer service persona named "Sarah, Customer Success Manager at TechCorp" with a custom prompt, voice selection, interruption threshold tuning, and ambient background audio.
3. **Send a Call with a Persona.** Dispatch a phone call using the `persona_id` parameter so the persona's settings serve as the baseline, and demonstrate how to override specific settings on a per-call basis.

## What Are Personas?

Personas are unified AI agent configurations that let you manage multiple phone numbers and use cases from a single, centralized definition. Instead of configuring voice, prompt, model, and behavior settings individually for every phone call or phone number, you create one persona that holds all of those settings together.

Key benefits of personas:

- **Centralized management.** Define your agent's personality, voice, prompt, and tools in one place. Every call that references the persona inherits those settings automatically.
- **Smart routing.** A persona can direct conversations based on context, making it possible to handle different caller intents through a single agent definition.
- **Version management.** Test changes in a draft version before promoting them to production. This prevents untested updates from reaching live callers.
- **Multi-channel deployment.** Apply one persona across multiple phone numbers. Update the persona once and the change propagates everywhere.
- **API integration.** Reference a persona with a single `persona_id` parameter in your API calls. No need to repeat the full configuration each time.

## Available Voices

Bland AI provides a library of voices you can use with your agents. Each voice has a unique tone and style. Some popular options include:

| Voice    | Description                |
| -------- | -------------------------- |
| Maya     | Popular female voice       |
| Ryan     | Popular male voice         |
| Mason    | Popular male voice         |
| Tina     | Female voice               |
| Josh     | Male voice                 |
| Florian  | Male voice                 |
| Derek    | Male voice                 |
| June     | Female voice               |
| Nat      | Female voice               |
| Paige    | Female voice               |

### How to Pick a Voice

1. **Run the `list_voices` script** in this cookbook to see every voice available on your account, including descriptions, tags, and ratings.
2. **Filter by "Bland Curated" tag.** Voices tagged as "Bland Curated" have been optimized for phone call audio quality and are the recommended starting point.
3. **Test a few candidates.** Send short test calls with different voices to hear how they sound in practice. Voice quality can vary depending on the prompt style and conversation flow.
4. **Consider your audience.** Match the voice to your brand and use case. A warm, friendly voice works well for customer service, while a confident, authoritative voice may be better for sales outreach.

### Voice Cloning

If none of the built-in voices match your needs, you can create a custom voice clone by uploading audio samples.

**Endpoint:** `POST https://api.bland.ai/v1/voices`

Upload clear, high-quality audio recordings of the target voice. The API processes the samples and creates a new voice entry that you can reference by name in your calls and personas. Tips for best results:

- Use studio-quality recordings with minimal background noise.
- Provide at least 30 seconds to 2 minutes of speech.
- Include varied intonation and pacing so the clone captures the full range of the speaker's voice.
- The cloned voice will appear in your voice list and can be used like any built-in voice.

## Creating a Persona Step by Step

### Step 1: Choose a Voice

Browse the voice catalog using the `list_voices` script or the Bland dashboard. Pick a voice that matches the personality you want your agent to project.

### Step 2: Write the Prompt

The `prompt` field is the heart of your persona. It defines the agent's personality, knowledge, goals, and behavioral rules. Write it as if you were briefing a new employee:

- Who are they? (Name, role, company)
- What is their goal on each call?
- What information should they collect or provide?
- What tone should they use?
- What should they never do?

### Step 3: Configure Behavior Settings

Fine-tune how the agent interacts with callers:

- **`first_sentence`**: The exact greeting the agent says when the call connects. Set this for consistency.
- **`interruption_threshold`**: Controls how sensitive the agent is to being interrupted. A lower value (e.g., 50) means the agent pauses more quickly when the caller starts speaking. A higher value (e.g., 200) means the agent is harder to interrupt. Tune this based on the conversation style you want.
- **`wait_for_greeting`**: Set to `true` if the agent should wait for the caller to speak first (common for inbound calls). Set to `false` if the agent should greet the caller immediately (common for outbound calls).
- **`model`**: Choose `"base"` for full feature support or `"turbo"` for lowest latency.
- **`background_track`**: Add ambient audio like `"office"` or `"cafe"` for a more natural feel.

### Step 4: Create the Persona via the API

Send a POST request to `https://api.bland.ai/v1/personas` with your configuration. The API returns a `persona_id` that you will use in all future calls.

See `create_persona.py` or `createPersona.js` for a complete working example.

### Step 5: Test the Persona

Send a test call using `send_call_with_persona.py` or `sendCallWithPersona.js`. Listen to the call, review the transcript in the Bland dashboard, and iterate on the prompt and settings until you are satisfied.

## Using persona_id in Calls

Once you have created a persona, sending a call with it is simple. Instead of passing the full configuration in every API call, you pass just the `persona_id`:

```json
{
  "phone_number": "+15551234567",
  "persona_id": "your-persona-id-here"
}
```

The persona's settings (prompt, voice, model, interruption threshold, and everything else) are applied automatically as the baseline for the call.

### Overriding Persona Settings

You can override any persona setting on a per-call basis by including additional parameters in the API request. Parameters you include in the call body take precedence over the persona defaults. For example:

```json
{
  "phone_number": "+15551234567",
  "persona_id": "your-persona-id-here",
  "first_sentence": "Hi! I am calling about your recent support ticket.",
  "max_duration": 10
}
```

In this example, the `first_sentence` and `max_duration` come from the call request, while everything else (voice, prompt, model, etc.) comes from the persona.

## Pronunciation Guides

When your agent needs to say brand names, acronyms, or unusual words correctly, use the `pronunciation_guide` parameter. This works in both direct calls and persona configurations.

```json
{
  "pronunciation_guide": [
    {
      "word": "ACME",
      "pronunciation": "Ak-mee",
      "case_sensitive": false,
      "spaced": false
    },
    {
      "word": "TechCorp",
      "pronunciation": "Tek-corp",
      "case_sensitive": true,
      "spaced": false
    },
    {
      "word": "SQL",
      "pronunciation": "sequel",
      "case_sensitive": false,
      "spaced": false
    }
  ]
}
```

Each entry in the array has four fields:

| Field            | Type    | Description                                                                                                 |
| ---------------- | ------- | ----------------------------------------------------------------------------------------------------------- |
| `word`           | string  | The word or phrase to match in the agent's output text.                                                      |
| `pronunciation`  | string  | How the agent should say it. Write it phonetically.                                                         |
| `case_sensitive` | boolean | If `true`, only matches the exact casing. If `false`, matches regardless of case.                           |
| `spaced`         | boolean | If `true`, the word is spelled out letter by letter (e.g., "A C M E"). If `false`, spoken as a single word. |

## Version Management: Draft vs. Production

Personas support version management so you can test changes safely before they go live.

### How It Works

1. **Create a persona.** The initial version is your production configuration.
2. **Update with draft changes.** Use the PATCH endpoint to modify the persona. You can test these changes by referencing the persona in test calls.
3. **Review and validate.** Send test calls, listen to the results, and refine the prompt or settings.
4. **Promote to production.** Once you are satisfied with the draft, promote it so all phone numbers using this persona pick up the new configuration.

This workflow prevents untested prompt changes from reaching live callers. You can iterate freely on drafts knowing that production calls are unaffected until you explicitly promote.

### Updating a Persona

Use the PATCH endpoint to update specific fields without replacing the entire configuration:

```
PATCH https://api.bland.ai/v1/personas/{persona_id}
```

Only include the fields you want to change:

```json
{
  "prompt": "Updated prompt text here...",
  "voice": "ryan"
}
```

Fields you omit remain unchanged.

## Multi-Number Deployment

Personas make it straightforward to run the same agent across multiple phone numbers.

1. **Create one persona** with the desired configuration.
2. **Assign it to multiple phone numbers** in the Bland dashboard, or reference the `persona_id` in API calls from different numbers.
3. **Update once, propagate everywhere.** When you update the persona, every phone number using it automatically gets the updated configuration.

This is especially useful for businesses with regional phone numbers, multiple departments, or white-label deployments where the same agent logic should be consistent across all numbers.

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

# Step 1: Browse available voices
python list_voices.py

# Step 2: Create a persona
python create_persona.py

# Step 3: Copy the persona_id from the output, add it to .env, then send a call
python send_call_with_persona.py
```

### Node.js

```bash
cd node
npm install axios dotenv
cp .env.example .env
# Edit .env and add your API key and phone number

# Step 1: Browse available voices
node listVoices.js

# Step 2: Create a persona
node createPersona.js

# Step 3: Copy the persona_id from the output, add it to .env, then send a call
node sendCallWithPersona.js
```

## API Reference

### List Voices

**Endpoint:** `GET https://api.bland.ai/v1/voices`

**Headers:**

| Header          | Value          | Description                    |
| --------------- | -------------- | ------------------------------ |
| `Authorization` | `YOUR_API_KEY` | Your Bland API key (no prefix) |

**Response:**

Returns an array of voice objects, each containing:

| Field            | Type    | Description                                                        |
| ---------------- | ------- | ------------------------------------------------------------------ |
| `id`             | string  | Unique voice identifier (UUID).                                    |
| `name`           | string  | Voice name, usable in call parameters.                             |
| `description`    | string  | Short description (e.g., "Young American Female").                 |
| `public`         | boolean | `true` if universally available, `false` if account-specific.      |
| `tags`           | array   | Descriptive labels including language and quality indicators.      |
| `total_ratings`  | number  | Total number of ratings this voice has received.                   |
| `average_rating` | number  | Average user rating.                                               |

### Create Persona

**Endpoint:** `POST https://api.bland.ai/v1/personas`

**Headers:**

| Header          | Value              | Description                    |
| --------------- | ------------------ | ------------------------------ |
| `Authorization` | `YOUR_API_KEY`     | Your Bland API key (no prefix) |
| `Content-Type`  | `application/json` | Required for JSON body         |

**Body Parameters:**

| Parameter                | Type    | Description                                                                        |
| ------------------------ | ------- | ---------------------------------------------------------------------------------- |
| `name`                   | string  | Display name for the persona.                                                      |
| `prompt`                 | string  | Global prompt describing personality, behaviors, and motivations.                  |
| `voice`                  | string  | Voice selection (use a name from the voice catalog).                               |
| `language`               | string  | Language preference (e.g., `"babel-en"`).                                          |
| `first_sentence`         | string  | Opening greeting when the call connects.                                           |
| `interruption_threshold` | number  | Response timing sensitivity. Lower values make the agent easier to interrupt.      |
| `wait_for_greeting`      | boolean | Whether to speak first (`false`) or wait for the caller (`true`).                  |
| `model`                  | string  | `"base"` (full features) or `"turbo"` (lowest latency).                            |
| `tools`                  | array   | Custom tools the agent can invoke during a call.                                   |
| `webhook`                | string  | URL to receive a POST request with call data when each call completes.             |
| `knowledge_base_ids`     | array   | IDs of connected knowledge bases for the agent to reference.                       |
| `pathway_id`             | string  | Pathway to use for structured conversation flows.                                  |
| `background_track`       | string  | Ambient sound. Options: `"office"`, `"cafe"`, `"restaurant"`, `"none"`, or `null`. |
| `analysis_schema`        | object  | Schema defining post-call analysis fields.                                         |

### List Personas

**Endpoint:** `GET https://api.bland.ai/v1/personas`

Returns all personas on your account.

### Get Persona

**Endpoint:** `GET https://api.bland.ai/v1/personas/{persona_id}`

Returns full details of a specific persona.

### Update Persona

**Endpoint:** `PATCH https://api.bland.ai/v1/personas/{persona_id}`

Same body fields as create. Only include the fields you want to update.

### Send Call with Persona

**Endpoint:** `POST https://api.bland.ai/v1/calls`

```json
{
  "phone_number": "+15551234567",
  "persona_id": "your-persona-id"
}
```

The persona's settings serve as the baseline. Any additional parameters in the request body override the persona defaults.

## Verifying It Works

Follow this sequence to confirm everything is set up correctly:

1. **List voices.** Run `list_voices.py` (or `listVoices.js`). You should see a formatted table of available voices. Confirm that Bland Curated voices appear in the filtered output.

2. **Create a persona.** Run `create_persona.py` (or `createPersona.js`). You should see output like:

   ```
   Persona created successfully!
   Persona ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   Name: Sarah, Customer Success Manager at TechCorp
   Voice: maya
   ```

   Copy the persona ID.

3. **Send a call.** Add the persona ID to your `.env` file as `PERSONA_ID`, then run `send_call_with_persona.py` (or `sendCallWithPersona.js`). Your phone should ring within a few seconds. Answer it and confirm the agent uses the persona's voice, greeting, and personality.

4. **Check results.** After the call ends, check the Bland dashboard under the Calls tab. Verify that:
   - The transcript matches the persona's expected behavior.
   - The voice matches what you selected.
   - The analysis schema (if configured) produced the expected output.

## Troubleshooting

### "Authorization header is missing or invalid"

Your API key is not being sent correctly. Double-check that:
- Your `.env` file contains the correct key with no extra spaces or quotes.
- The key starts with the expected prefix (usually `sk-`).
- The `.env` file is in the same directory as the script you are running.

### "Persona not found"

The `persona_id` does not match any persona on your account. Verify that:
- You copied the full persona ID from the create response.
- The persona was created under the same account as the API key you are using.
- The persona has not been deleted.

### The agent does not use the persona's voice or prompt

Make sure you are passing `persona_id` (not `persona`) in the request body. Also check that you are not accidentally overriding the `voice` or `task` fields in the same request, which would replace the persona defaults.

### Voice not found

The voice name must exactly match a voice in your catalog. Run the `list_voices` script to see all available names. Voice names are case-sensitive.

### "Module not found" errors

Make sure you have installed the dependencies:
- Python: `pip install requests python-dotenv`
- Node.js: `npm install axios dotenv`

## Next Steps

Now that you have personas and voices set up, explore these ideas:

- **Clone a voice.** Upload audio samples to create a custom voice that matches your brand exactly.
- **Add knowledge bases.** Connect a knowledge base to your persona so the agent can answer detailed questions from your documentation.
- **Use pathways.** Combine a persona with a pathway for structured, multi-step conversation flows.
- **Set up analysis schemas.** Define post-call analysis fields to automatically extract structured data from every conversation.
- **Deploy across multiple numbers.** Assign your persona to several phone numbers for consistent agent behavior across your organization.

Check out the other cookbooks in this series for more advanced use cases like batch campaigns, custom tools, and SMS messaging.
