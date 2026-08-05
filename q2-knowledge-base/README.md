# Question 2: Production-Ready Knowledge Base

This folder now contains a working, runnable knowledge-base prototype.

## What it does

- ingests messy business text from local source files
- cleans boilerplate and duplicate content
- masks obvious PII
- splits content into source-traceable records
- builds a searchable JSON knowledge base
- answers test queries with ranked retrieval results

## Folder structure

- `data/raw/`: sample source documents
- `out/`: generated knowledge base artifacts
- `src/`: builder and retrieval code
- `tests/`: retrieval test cases and scripts

## Why this design

The assessment asks for something production-aware, so the implementation focuses on:

- traceability: every record keeps source metadata
- reliability: answers come from retrieved records, not invented text
- cleanliness: boilerplate, duplicates, and obvious PII are handled
- portability: no heavy external dependencies are required

## How to run

From this directory:

```powershell
python .\src\cli.py build
python .\src\cli.py query "What documents are needed for branch partnership onboarding?"
python .\src\cli.py test
```

## Included sample sources

The sample sources are intentionally messy enough to show real processing:

- website-style content
- FAQ content
- policy text with repeated sections
- examples containing obvious PII patterns to mask

## Output artifacts

The build command writes:

- `out/kb.json`: canonical records
- `out/index.json`: lightweight retrieval index
- `out/build-report.json`: summary of cleaning decisions

