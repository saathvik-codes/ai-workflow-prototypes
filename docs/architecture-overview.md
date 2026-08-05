# Architecture Overview

## Overall system

```mermaid
flowchart TD
  raw[Raw business sources] --> kb[Q2 KB builder]
  kb --> kbjson[Structured KB JSON]
  kbjson --> q1[Q1 grounded voice agent]
  kbjson --> q3[Q3 localized voice bots]
  stream[Live or replayed call audio] --> q4[Q4 streaming insight pipeline]
  q4 --> nudge[Real-time nudge output]
```

## Design principle

The main design choice is to keep source of truth separate from generation:

- Q2 owns the canonical knowledge structure.
- Q1 consumes that knowledge and stays grounded.
- Q3 focuses on language and market realism.
- Q4 focuses on live signal extraction and timing.

