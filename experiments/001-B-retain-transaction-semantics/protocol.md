# Probe 001-B — source-aware retain transaction semantics

Status: THROWAWAY / LOCAL SEMANTIC SAFETY PROBE

## Problem

A ChatGPT Skill can write through an App before the final response, but no public host-level post-final callback has been established. A pre-final write can therefore outlive an interrupted response.

## Key split

Do not treat all retention candidates alike.

| Source class | Can become active before final response? | Reason |
|---|---:|---|
| `USER_ASSERTED` | yes | the current user message is already the evidence event |
| `EXTERNAL_VERIFIED` | yes | an independently observed external postcondition is the evidence event |
| `USER_APPROVED_DECISION` | yes | the user's approval message is already the commitment event |
| `ASSISTANT_DERIVED` | no | the durable claim depends on assistant interpretation/delivery |
| `INFERRED_PREFERENCE` | no | requires explicit approval or later corroboration |

## Generic transaction states

```text
candidate
  -> ACTIVE       source-anchored fact with durable write + readback
  -> PENDING      assistant-derived / inferred candidate

PENDING
  -> CONFIRMED    later turn can reconcile against visible conversation/evidence
  -> SUPERSEDED   later evidence replaces candidate
  -> ABANDONED    candidate cannot be reconciled or is contradicted
```

`PENDING` must never be injected as current fact by default.

## Failure rules

1. Final response interrupted after a `USER_ASSERTED` write: memory may remain active because the user message itself is provenance.
2. Final response interrupted after an `EXTERNAL_VERIFIED` write: memory may remain active if the external postcondition was independently verified.
3. Final response interrupted after an `ASSISTANT_DERIVED` stage: candidate remains pending and cannot become active merely because it was written.
4. Search miss while looking for a pending transaction means transaction state is UNKNOWN, not absent/complete.
5. Duplicate stage calls must not create two active facts. Providers without exact/idempotent keys degrade to append-only duplicate detection on later recall.
6. A successful App call is not sufficient persistence proof when independent readback is available.

## Provider capability mapping from current ChatGPT tool schemas

### Basic Memory Cloud

Useful primitives:
- `search_notes` with metadata/status/tags and exact title/permalink modes;
- `fetch` by permalink/title/memory URL;
- `write_note` with JSON response, metadata, tags, and explicit overwrite policy.

Disposition: `STRONG` for transaction receipts/readback. Prefer immutable stage + immutable confirmation notes instead of silently overwriting semantic history.

### ButlerBrain

Useful primitives:
- `search_brain(query, table, sort=relevance|recency)`;
- `save_thought(text, owner, tags, private)`.

Observed schema does not expose exact fetch-by-id, update, delete, or tag-filter lookup.

Disposition: `DEGRADED_BUT_USABLE` for append-only transactions. Put a unique transaction key in text/tags and append a confirmation/supersession receipt; semantic search remains weaker than exact addressing.

## Consequence

The shim should retain **durable deltas with typed provenance**, not mirror the whole assistant turn. Lossless transcript synchronization still needs a host lifecycle or a separate history source.
