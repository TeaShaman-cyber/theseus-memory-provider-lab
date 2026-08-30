# Provider App Contract v0 — research proposal

This is a research interface, not an implemented API.

## Principle

Keep user identity, provider namespace, transaction ids, and exact persistence receipts on the App/backend side. Keep semantic selection policy in the Skill.

## Minimal operations

### `memory_recall`

Input:

```json
{
  "query": "current user turn / unresolved referent",
  "limit": 5
}
```

Backend responsibilities:
- resolve authenticated user/provider namespace;
- apply provider-specific search;
- return bounded memories with stable ids, provenance, and lifecycle state;
- exclude `pending/abandoned/superseded` from current recall by default.

Output shape:

```json
{
  "items": [
    {
      "id": "stable-id",
      "content": "...",
      "state": "active",
      "source": "...",
      "evidence_ref": "..."
    }
  ],
  "receipt": "recall-receipt-id"
}
```

### `memory_retain`

Input:

```json
{
  "delta": "compact durable memory candidate",
  "source_class": "USER_ASSERTED|EXTERNAL_VERIFIED|USER_APPROVED_DECISION|ASSISTANT_DERIVED|INFERRED_PREFERENCE",
  "provenance": "source/evidence pointer"
}
```

Backend responsibilities:
- bind authenticated identity and configured namespace;
- allocate transaction/idempotency id;
- choose initial state from source class or accept a policy-safe requested state;
- durably write before returning success.

Output:

```json
{
  "transaction_id": "tx-id",
  "record_id": "record-id",
  "state": "active|pending",
  "write_receipt": "receipt-id"
}
```

### `memory_readback`

Input: exact `transaction_id` or `record_id`.

Output: exact persisted record + lifecycle state + provenance.

No semantic search is sufficient for this postcondition.

### `memory_reconcile` (optional but valuable)

Append a confirmation, contradiction, supersession, or abandonment disposition for a pending candidate. Prefer append-only lifecycle evidence over destructive rewrite.

## Skill/backend boundary

Skill decides:
- whether recall is useful on this non-trivial turn;
- which recalled evidence matters;
- whether a durable delta emerged;
- source class and provenance.

Backend decides:
- who the user is;
- where memory is stored;
- transaction/idempotency identity;
- durable write/readback mechanics;
- provider-specific indexing and privacy enforcement.

This separation is the closest model-mediated analogue to Hermes `MemoryProvider` without pretending ChatGPT exposes host lifecycle callbacks.
