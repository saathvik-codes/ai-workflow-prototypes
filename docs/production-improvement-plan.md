# Production Improvement Plan

This repository is intentionally lightweight so it can run locally without special infrastructure. If this were moved into a real production environment, the next improvements would be:

## Question 1

- integrate a real telephony provider
- replace local web calling with a hosted call widget or phone number
- stream transcripts from live ASR
- persist call metadata and handoff events
- use the KB retriever as a service instead of a local file

## Question 2

- add OCR and HTML parsers for richer source types
- store embeddings in a vector database
- add source versioning and rollback support
- expand PII detection with named-entity redaction

## Question 3

- connect real ASR/TTS providers for both markets
- add market-specific pronunciation testing
- use prompt templates per language and line of business
- run native-speaker review on recurring samples

## Question 4

- consume live audio over WebSocket or streaming API
- separate agent and customer diarization
- measure end-to-end latency in a real telemetry system
- run alert suppression and false-positive review at scale
