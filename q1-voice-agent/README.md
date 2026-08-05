# Question 1: Knowledge-Grounded Voice Agent

This is a runnable voice-agent simulation for health-insurance lead qualification.

The prompt allowed choosing one use case from the listed options. This project selects
health-insurance lead qualification and keeps the other options, such as business-loan
qualification, candidate screening, insurance renewal-only flows, and loan pre-due
reminders, as explicit safe-routes/escalations instead of pretending those workflows
are fully implemented.

## What it demonstrates

- grounded answers sourced from the Question 2 knowledge base
- qualification flow with incomplete/conflicting detail handling
- objection handling without hardcoding the entire FAQ set
- unsupported-question fallback
- human escalation
- optional lead summary output

## Files

- `src/`: agent logic and CLI
- `scenarios/`: test call scripts
- `out/`: generated transcripts and summaries

## How to run

From this directory:

```powershell
python .\src\cli.py run .\scenarios\cooperative.json
python .\src\cli.py run .\scenarios\objection.json
python .\src\cli.py run .\scenarios\out_of_scope.json
python .\src\cli.py test
```

## Design choice

The agent does not rely on a giant system prompt. Instead, it:

1. classifies the user message
2. retrieves relevant KB entries
3. generates a grounded response
4. escalates when confidence or scope is weak

No paid API key is required for the local prototype because the web calling interface
is used instead of a PSTN number. Real telephony, ASR, and TTS provider credentials are
documented as optional production integrations in the root `.env.example`.
