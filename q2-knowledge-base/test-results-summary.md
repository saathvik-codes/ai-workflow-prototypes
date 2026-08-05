# Retrieval Test Summary

This summary reflects the current Q2 knowledge-base retrieval behavior verified against `q2-knowledge-base/out/kb.json`.

## Verified categories

The KB contains grounded records for the following intents:

- product plans
- family coverage
- claims
- policy renewal
- qualification rules
- objection handling
- PII handling
- partnership benefits

## Retrieval validation

The following checks were run against the built KB and returned the expected top category:

- `What is covered under family insurance?` -> `family_coverage`
- `How can I submit an insurance claim?` -> `claims`
- `Am I eligible if I am 27 years old?` -> `qualification_rules`
- `The premium seems expensive.` -> `objection_handling`
- `Renwel` -> `policy_renewal`
- `Who won yesterday's IPL match?` -> no relevant information available
- `John Doe` -> `pii_handling`
- `Coverage Benefits okay` -> `partnership_benefits`

## Notes

- The typo case is handled by the retriever's normalization logic, which maps the misspelling to the renewal intent.
- Unknown or out-of-domain queries return no hits instead of fabricating an answer.
- PII-related content is masked in the source data and routed to the `pii_handling` category.

## Current assessment status

The retrieval checks are behaving correctly for the sample queries and the additional validation queries above.
