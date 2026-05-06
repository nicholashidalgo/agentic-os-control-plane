# Agent Memory Patterns

Notes on how AI agents can manage persistent memory across sessions without relying on a live context window.

## Short-Term vs Long-Term Memory

Most agent frameworks treat memory as either in-context (short-term) or external (long-term). The challenge is deciding when to promote information from one tier to the next, and how to avoid accumulating noise in long-term storage.

Key tensions:
- Recency bias: agents tend to over-weight recent context
- Retrieval cost: embedding-based recall adds latency and token cost
- Staleness: stored facts become incorrect as the world changes

## Vault-Based Memory Model

A vault-based approach uses the filesystem as the memory substrate:

- `raw/` holds unstructured notes as they arrive — no curation required
- `wiki/` holds promoted, structured documents — curated by a cleanup skill
- `projects/` holds active working context for ongoing initiatives
- `daily/` holds session logs and handoff briefs

Promotion happens through explicit policy (e.g., "2+ headings = promote to wiki") rather than embedding similarity, which makes behavior predictable and auditable.

## Continuation Protocols

A continuation brief is a structured handoff document written at the end of each session. It captures:

- Current focus and open tasks
- Key decisions made
- Files changed
- Context needed to resume

This pattern allows a stateless agent to resume work across sessions without requiring a persistent process or long-running memory server.

## Trade-offs

- **Predictability vs flexibility**: rule-based promotion is easy to audit but misses nuanced relevance
- **Local vs vector store**: filesystem is zero-dependency but lacks semantic search
- **Agent-written vs human-written**: agent-generated wiki entries may require editorial review

These trade-offs suggest a hybrid: local vault for structured artifacts, optional vector index for unstructured retrieval, with the vault as the source of truth.
