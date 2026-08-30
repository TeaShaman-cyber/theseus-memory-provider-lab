# Probe 001-D — provider adapter fit

Status: PUBLIC / TOOL-SCHEMA INTERFACE ANALYSIS

## Target model-mediated provider contract

A provider should let the Skill do four things without inventing user identity or persistence state:

1. bounded recall;
2. durable staged retain;
3. exact readback by transaction/record id;
4. lifecycle disposition (`active`, `pending`, `superseded`, `abandoned`) with provenance.

## Observed interface classes

| Capability | ButlerBrain-style surface | Basic Memory-style surface |
|---|---|---|
| Semantic/text recall | semantic brain search | text/semantic search plus context building |
| Durable write | append thought | addressed note write |
| Exact addressed readback | not exposed in the observed surface | exact fetch by stable note identifier is exposed |
| Metadata/status filtering | limited in observed recall surface | metadata/status/tag filters are exposed |
| Update/replace | not exposed in observed surface | addressed overwrite exists; append-only lifecycle receipts remain preferable |
| Identity binding | observed calls contain explicit identity arguments | namespace/project routing is more server/config driven |
| Safe idempotent retain | degraded without exact receipt lookup | feasible with deterministic addressing + exact fetch |

No private identity values or account-specific permission settings are part of this public matrix.

## ButlerBrain-oriented gap

The observed connector surface is strong for semantic recall and append-only durable writes, but a robust automatic provider benefits from authenticated identity binding on the backend and an exact transaction receipt/readback primitive.

Suggested provider-oriented shape:

```text
memory_retain(delta, source_class, provenance)
-> { transaction_id, record_id, state }

memory_readback(transaction_id)
-> exact persisted record/receipt
```

Semantic search remains appropriate for recall. It should not be the only verification primitive for a just-written transaction.

## Basic Memory-oriented gap

Addressed readback and metadata-aware retrieval already fit the transaction model well. The main always-on concern is deterministic namespace/project scope: automatic retention must not spray durable state across projects based on model guesswork.

## Permission boundary

Permission configuration is deployment/account specific and is intentionally excluded from public evidence. Even where writes can execute without UI confirmation, provider enablement and retention policy remain explicit user choices.
