# Knowledge Base Design Notes

## Schema

The generated records use a stable JSON structure:

- `record_id`
- `title`
- `content`
- `category`
- `source`
- `source_ref`
- `version`
- `pii_present`
- `chunk_index`
- `tags`

## Versioning

- Source files are treated as versioned inputs.
- The `version` field on each record marks the content generation version.
- A future production deployment would store source hash, build timestamp, and rollback history.

## Embedding and indexing approach

This prototype uses lightweight lexical retrieval with BM25-style scoring for portability and transparency.

In production, the same schema would support:

- vector embeddings for semantic recall
- keyword or BM25 indexing for exact policy terms
- hybrid ranking that blends semantic and lexical signals

## Retrieval ranking logic

Ranking prefers:

1. category match
2. token overlap with the query
3. tag overlap
4. query-specific boosts for known intent patterns

## Citation method

Every result keeps `source_ref` so the downstream agent can cite the original source file or document location instead of inventing a reference.

## Traceability rules

- duplicate or near-duplicate chunks are removed
- boilerplate is stripped before indexing
- PII-related content is flagged and masked

