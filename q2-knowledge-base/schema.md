# Knowledge Base Schema

## Record model

```json
{
  "record_id": "kb_product_001",
  "title": "Branch Partnership Benefits",
  "content": "Operational, marketing, and technology support is provided to branch partners.",
  "category": "partnership_benefits",
  "source": "website section",
  "source_ref": "docs/company-site/partnerships.html",
  "version": "1.0",
  "pii_present": false,
  "chunk_index": 0,
  "tags": ["partnership", "benefits", "operations"]
}
```

## Design rules

- One record should answer one coherent user intent.
- Source references must remain attached after chunking.
- If a source contains duplicated language, keep the canonical version and link duplicates back to it.
- Any PII should be masked or excluded unless explicitly needed and approved.

## Metadata priorities

1. source trust level
2. category
3. version
4. recency
5. semantic relevance

