# Architecture

## Program relationship

`theseus-research` is the public-interest research program contract and root registry. This repository is one execution/research line beneath it.

```text
theseus-research
        ↓
theseus-memory-provider-lab
```

## Target boundary

The research separates two mechanisms that can look similar to a user:

```text
model-mediated
Skill → App calls → memory
```

versus:

```text
host-mediated
prefetch callback → model → post-turn sync callback
```

The first can approximate useful memory-provider behavior. It must not be described as the second without observed host lifecycle support.

## Proposed model-mediated contract

```text
memory_recall(query, limit)
  -> bounded active memories + provenance + receipt

memory_retain(delta, source_class, provenance)
  -> transaction_id + record_id + initial lifecycle state

memory_readback(transaction_id | record_id)
  -> exact persisted record

memory_reconcile(transaction_id, disposition)
  -> optional append-only lifecycle transition
```

Backend responsibilities include authenticated identity, namespace selection, transaction/idempotency identity, privacy enforcement, and durable persistence receipts. The Skill decides semantic relevance, source class, and whether a durable delta exists.

## Source-aware retain

```text
USER_ASSERTED           → ACTIVE after durable readback
EXTERNAL_VERIFIED       → ACTIVE after durable readback
USER_APPROVED_DECISION  → ACTIVE after durable readback
ASSISTANT_DERIVED       → PENDING
INFERRED_PREFERENCE     → PENDING
```

`PENDING` is not current fact and is excluded from normal recall by default.

## Authority rule

Persistent memory is a continuity/evidence layer. Current operational questions still require the authoritative live source when freshness matters.
