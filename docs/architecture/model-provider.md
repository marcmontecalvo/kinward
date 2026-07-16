# Model Provider Architecture

Kinward generates conversation replies through a neutral `ModelProvider` port
(`services/kinward/src/kinward/llm/contracts.py`), never a vendor SDK called
directly from `application/conversation.py`.

Required operation:

- Generate a reply from a system prompt and a message history.

## Native implementations

- `OpenAiCompatibleModelProvider` - OpenAI's own API and any self-hosted server that speaks
  the OpenAI chat-completions wire format (Ollama, vLLM, llama.cpp server, LM Studio, ...).
  `base_url` is the API root including any version prefix the server expects (e.g.
  `https://api.openai.com/v1` or `http://ollama.local:11434/v1`).
- `AnthropicModelProvider` - Anthropic's Messages API (`base_url` e.g. `https://api.anthropic.com/v1`).
- `NullModelProvider` - the truthful degraded state when no provider is configured or reachable;
  it never fabricates a reply.

## Provider selection

Provider, base URL, model name, and API key are admin-editable, per-household settings stored
in `ProviderSettingsRecord`, changed from the Kinward integration's options flow in Home
Assistant - the same screen and the same DB row that select the memory/knowledge backends (see
`memory-and-knowledge.md`). The API key is never echoed back by the settings API (only whether
one is set); the options flow can set or replace it but leaving the field blank on resubmit
always means "keep the current one," never "clear it," since the form has no way to show the
current value to prefill against.

Storing the API key in the same SQLite database as the rest of household state is a stopgap:
`ARCHITECTURE-SPINE.md`'s AD-12 (envelope-encrypted credentials) is adopted but not yet built.
Once it exists, this key moves under that envelope like other provider credentials.

## Conversation grounding

Each turn folds three optional context sources into the system prompt before calling the model:

- Recent Home Assistant entity state (via the existing `HomeAssistantClient`, read-only,
  capped and compacted - not a new HA connection setting, since that client's own
  `home_assistant_url`/`home_assistant_token` are unchanged deployment `Settings`).
- A resolved "most recently changed light/switch" and "currently active timer," when one exists
  - a v0 heuristic for ADR-002's operational household context, see
  `docs/architecture/operational-household-context.md`. Read-only description only; nothing here
  can yet act on a device or timer (see that doc's "what remains out of scope").
- Conversational memory recall from the configured memory backend.
- Household fact search from the configured knowledge backend.

Writing new facts from a conversation (knowledge *proposal*, not search) is not wired here -
that requires structured extraction and confirmation policy (epics.md Stories 4.3/4.4), which
remains unbuilt.

## Replacement boundary

A future model implementation must satisfy the neutral protocol in:

```text
services/kinward/src/kinward/llm/contracts.py
```

Core assistant and orchestration code depends on that protocol, never a vendor-specific
request/response shape.
