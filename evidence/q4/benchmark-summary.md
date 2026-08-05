# Q4 Benchmark Summary

## Normal call

- Missed cross-sell is detected.
- Frustration is detected.
- Callback need is detected.
- Nudges are emitted once per signal type.

## Noisy call

- No unnecessary nudges are produced.
- Duplicate or low-value alerts are suppressed.

## Latency

- The simulated pipeline stays around 10 ms per chunk in this local benchmark.
- P50 and P95 are both reported in the JSON output.

