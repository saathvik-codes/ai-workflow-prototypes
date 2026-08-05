# Submission Checklist

## Before sharing

- Run `q2-knowledge-base` build and retrieval tests
- Run `q1-voice-agent` scenario tests
- Run `q1-voice-agent serve` and exercise `POST /call`
- Run `demo-server` and manually test `/q1`, `/q2`, `/q3`, and `/q4`
- Run `q3-localized-bots` tests
- Run `q4-live-insights` benchmark
- Review `docs/requirement-coverage-matrix.md`
- Review all generated evidence summaries

## What to say in the walkthrough

- The KB is the source of truth for grounded answers.
- The voice agent does not hardcode policy FAQs.
- The localized bots preserve natural market language.
- The live-insights engine emits nudges during the call, not after.
- The demo is local and credential-free; real telephony, ASR, and TTS integrations are called out as production next steps.
