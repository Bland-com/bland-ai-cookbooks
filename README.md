# Bland AI Cookbooks

Production-ready examples for building AI phone agents, web chat bots, and SMS conversations with the [Bland AI](https://www.bland.ai) API. Every cookbook includes both **Python** and **Node.js** examples with inline comments explaining each step.

## Prerequisites

1. **Create a Bland AI account** at [app.bland.ai](https://app.bland.ai)
2. **Grab your API key** from the developer portal dashboard
3. **Add credits** to your account (calls are billed at $0.12/min, to the exact second)

## Cookbooks

| # | Cookbook | What you will learn |
|---|---------|---------------------|
| 01 | [Getting Started](./01-getting-started/) | Send your first outbound call, poll for results, and read the transcript |
| 02 | [Inbound Calls](./02-inbound-calls/) | Buy a phone number, configure an AI agent to answer, and handle call routing |
| 03 | [Conversational Pathways](./03-pathways/) | Build multi-step conversation flows with branching logic, conditions, and variables |
| 04 | [Custom Tools](./04-custom-tools/) | Let your agent call external APIs mid-conversation (CRM updates, bookings, lookups) |
| 05 | [Web Chat Widget](./05-web-chat-widget/) | Embed an AI chat widget on any website with custom styling and live agent handoff |
| 06 | [Web Voice Agent](./06-web-voice-agent/) | Add a voice-powered AI assistant to your web app using the BlandWebClient SDK |
| 07 | [Speed to Lead](./07-speed-to-lead/) | Instantly call new leads from a webhook, qualify them, and push results to your CRM |
| 08 | [Appointment Scheduling](./08-appointment-scheduling/) | Build an agent that checks calendar availability and books meetings in real time |
| 09 | [Batch Campaigns](./09-batch-campaigns/) | Launch large-scale outbound campaigns with CSV uploads and dynamic personalization |
| 10 | [Call Analysis](./10-call-analysis/) | Extract structured insights from completed calls and set up post-call webhooks |
| 11 | [Personas and Voices](./11-personas-and-voices/) | Create reusable agent personas, pick voices, and clone custom voices |
| 12 | [SMS Messaging](./12-sms-messaging/) | Send and receive AI-powered text messages using the same phone numbers as voice |

## Quick Setup

### Python

```bash
pip install requests python-dotenv
```

### Node.js

```bash
npm init -y
npm install axios dotenv
```

### Environment Variables

Every cookbook expects a `.env` file in its folder (or in the repo root) with at least:

```
BLAND_API_KEY=sk-your-api-key-here
```

Some cookbooks need additional variables. Check each cookbook's README for details.

## Project Structure

```
bland-ai-cookbooks/
  01-getting-started/
    README.md
    python/
      send_call.py
      get_call.py
      .env.example
    node/
      sendCall.js
      getCall.js
      .env.example
  02-inbound-calls/
    ...
  (and so on for each cookbook)
```

## API Reference

Full API docs live at [docs.bland.ai](https://docs.bland.ai). The machine-readable index is at [docs.bland.ai/llms.txt](https://docs.bland.ai/llms.txt).

## Base URL

All API requests go to:

```
https://api.bland.ai
```

## Authentication

Every request needs your API key in the `Authorization` header:

```
Authorization: YOUR_API_KEY
```

Note: Bland uses the raw key directly, not a "Bearer" prefix.

## Support

- [Discord Community](https://discord.gg/QvxDz8zcKe)
- [Blog and Guides](https://www.bland.ai/blog)
- [Enterprise Inquiries](https://forms.default.com/361589)

## License

MIT
