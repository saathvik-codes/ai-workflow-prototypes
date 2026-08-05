# Assessment Analysis

This assessment is less about building a flashy demo and more about proving that the system can handle messy, real-world business inputs reliably.

## What the evaluator is looking for

- a working prototype, not just a design document
- grounded answers tied to a knowledge base
- safe fallback behavior when the system does not know something
- localized language handling rather than literal translation
- measurable latency and quality claims
- evidence that the candidate can explain the choices

## Shared themes across all questions

### 1. Reliability over creativity

The strongest submission will avoid pretending to know things. If a policy, FAQ, or instruction is missing, the system should say so clearly and escalate or defer.

### 2. Traceability

Every important answer should be connected to a source record, transcript, or structured rule. This matters for recruiter confidence and for real production review.

### 3. Separation of concerns

The assessment is easier to defend if each question is isolated:

- Question 1 focuses on live voice workflow
- Question 2 focuses on data cleaning and retrieval
- Question 3 focuses on localization and market realism
- Question 4 focuses on real-time analysis and nudges

### 4. Measured behavior

The submission should contain actual test outputs:

- call transcripts
- retrieval test cases
- latency measurements
- false-positive examples
- fallback and escalation examples

## Recommended implementation order

1. Build Question 2 first, because Question 1 depends on the knowledge base.
2. Build Question 1 using the KB from Question 2.
3. Build Question 3 as two localized prototypes with market-specific language behavior.
4. Build Question 4 as a streaming simulation or live pipeline with latency reporting.

## How to think about the final story

The final narrative should be:

1. We turned unstructured business content into a structured knowledge base.
2. We used that KB to ground a voice agent and prevent hallucinated answers.
3. We localized separate voice experiences for two financial markets.
4. We added real-time call intelligence with measurable latency and controlled nudging.

That story is recruiter-friendly because it shows product thinking, systems thinking, and applied AI judgment.

