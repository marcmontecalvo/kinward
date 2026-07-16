# Memory and Knowledge Architecture

Kinward separates conversational memory from curated factual knowledge.

## Conversational memory

`ConversationalMemoryProvider` owns interaction history and relationship continuity.

Required operations:

- Append messages.
- Recall relevant memories.
- Revise a memory.
- Forget a memory.
- Export a person-and-assistant memory scope.

The first native implementation is `HonchoMemoryProvider`, targeting a locally hosted Honcho v3 API.

Honcho is canonical for conversation history. Kinward does not duplicate the full message corpus in PostgreSQL. The local database may retain provider-neutral IDs, privacy metadata, source metadata, and lifecycle references.

Scopes are isolated by:

- Household workspace.
- Person peer.
- Assistant peer.
- Person-and-assistant session.

## Curated factual knowledge

`KnowledgeStoreProvider` owns durable, structured facts rather than raw conversation history.

Required operations:

- Propose a fact.
- Confirm a fact.
- Search facts.
- Revise a fact.
- Retire a fact.
- Retrieve provenance.

The first native implementation is `LlmWikiKnowledgeProvider`, targeting the locally hosted llm_wiki v1 workspace facts API.

llm_wiki is canonical for structured fact values, versions, confidence, status, and provenance. Kinward does not create a second semantic copy of the knowledge corpus.

## Provider selection

Which backend each capability uses is an admin-editable, per-household setting stored in
`ProviderSettingsRecord` (`persistence/models.py`), not a deployment-time env var - an
administrator changes it from the Kinward integration's options flow in Home Assistant, and
it takes effect on the next conversation turn without a backend restart. The equivalent
`KINWARD_MEMORY_BACKEND`/`KINWARD_HONCHO_URL`/`KINWARD_KNOWLEDGE_BACKEND`/`KINWARD_LLM_WIKI_URL`
env vars on `Settings` (`config.py`) only seed the health check's fallback view before a
household exists; `application/conversation.py` always reads the DB row.

Both capabilities default to `none`. Kinward must boot and provide core household functionality
without either service.

## Replacement boundary

A future conversational-memory or knowledge implementation must satisfy the neutral protocols in:

```text
services/kinward/src/kinward/memory/contracts.py
```

Core assistant, UI, privacy, and orchestration code must depend on those protocols rather than Honcho- or llm_wiki-specific API shapes.
