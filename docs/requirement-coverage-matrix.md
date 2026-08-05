# Requirement Coverage Matrix

## Question 1

- Configure the voice platform and add script/business rules
  - Implemented as a grounded local voice-agent simulation in `q1-voice-agent/src/agent.py` and `q1-voice-agent/src/cli.py`
  - Evidence: `q1-voice-agent/out/*.json`
- Connect the Q2 knowledge base
  - Implemented through KB loading and retrieval in `q1-voice-agent/src/agent.py`
  - Evidence: retrieval hit IDs in `q1-voice-agent/out/test-results.json`
- Conversation flow, qualification, objection handling, unsupported fallback, human escalation
  - Implemented in `q1-voice-agent/src/agent.py`
  - Evidence: scenario transcripts and test results
- Callable number or web calling interface
  - Implemented as a local web calling interface in `q1-voice-agent/src/cli.py serve`
  - Also exposed in the unified browser demo at `demo-server/src/server.py`
  - Endpoint: `POST /api/q1/call` or browser page `/q1`
  - Browser page supports text entry, microphone input where supported, speech playback, transcript history, and recording save.
- At least three test calls and transcripts
  - Implemented via scenario files in `q1-voice-agent/scenarios/*.json`
  - Evidence: generated transcripts in `q1-voice-agent/out/`
  - Browser recordings can be saved from `/q1` into `evidence/q1/recordings/`
  - Boundary: real PSTN phone calls require a telephony/voice platform credential.
- Optional business action
  - Implemented as mock CRM handoff generation in `q1-voice-agent/src/agent.py`
  - Includes preliminary eligibility, callback request flag, CRM stage, and next action
  - Excel-friendly CSV export is generated at `q1-voice-agent/out/mock_crm_export.csv`

## Question 2

- Data collection and cleaning
  - Implemented in `q2-knowledge-base/src/kb_builder.py`
- Knowledge-base design
  - Implemented in `q2-knowledge-base/schema.md` and `q2-knowledge-base/design-notes.md`
- Retrieval testing
  - Implemented in `q2-knowledge-base/tests/retrieval_cases.json` and `q2-knowledge-base/src/cli.py test`
- Connect KB to voice bot or retrieval interface
  - Implemented through Q1 KB usage

## Question 3

- Philippines bot with English, Filipino, Taglish
  - Implemented in `q3-localized-bots/src/philippines_bot.py`
- Indonesia bot with formal and colloquial Bahasa, finance loanwords, regional-accent tolerance
  - Implemented in `q3-localized-bots/src/indonesia_bot.py`
- ASR/TTS configuration and localization evidence
  - Documented in `q3-localized-bots/config.md`, `q3-localized-bots/examples.md`, and `q3-localized-bots/test-plan.md`
- Required test coverage
  - Implemented in `q3-localized-bots/src/cli.py test`

## Question 4

- Streaming input
  - Simulated in `q4-live-insights/src/pipeline.py`
- Streaming transcription and latency
  - Simulated per chunk with component metrics and speaker separation in `q4-live-insights/src/pipeline.py`
- Signal extraction and nudge generation
  - Implemented for topic shift, compliance/risk, frustration, buying signal, missed opportunity, and callback/payment need in `q4-live-insights/src/pipeline.py`
- Nudge control and false-positive suppression
  - Implemented via confidence threshold, duplicate suppression, topic grouping, priority, expiry, and noisy-call behavior
- Required test coverage
  - Implemented in `q4-live-insights/src/cli.py benchmark`
  - Also testable from the browser demo at `/q4`
