# Probe 003-A — acceptance, persistence, readback, and reconciliation

Status: LOCAL EXECUTABLE REFERENCE MODEL

Issue: `#3`

## Question

Can transaction/materialization state remain explicit and separate from semantic memory lifecycle when failures occur after acceptance?

## Versioned transaction table

`TRANSITION_TABLE_VERSION = 0.1`

```text
PROPOSED
  -> VALIDATED
  -> ACCEPTED
  -> PERSISTED
  -> READBACK_VERIFIED
  -> RECONCILED
```

Injected branch states:

```text
ACCEPTED            --write failure--> WRITE_FAILED
PERSISTED           --mismatch-------> READBACK_MISMATCH
READBACK_VERIFIED   --refresh failure-> RECONCILIATION_PENDING
```

Retries are allowed only from the corresponding retryable branch state. Reconciliation before verified readback is forbidden.

## Semantic axis

The reference model intentionally keeps semantic lifecycle separate:

```text
USER_ASSERTED
EXTERNAL_VERIFIED
USER_APPROVED_DECISION
    -> ACTIVE only after successful durable readback

ASSISTANT_DERIVED
INFERRED_PREFERENCE
    -> remain PENDING even after persistence and reconciliation
```

This is a research policy carried forward from issue #1, not a universal provider rule.

## Failure observations encoded by tests

| Injected failure | Provider content | Readback verified | Projection updated | Safe-source semantic state |
| --- | --- | --- | --- | --- |
| write failure | no | no | no | `PENDING` |
| readback mismatch | yes | no | no | `PENDING` |
| reconciliation failure | yes | yes | no | `ACTIVE` |

The third row is the key separation: a memory may be durably written and readback-verified while a derived projection remains unreconciled.

## Retry invariant

A retry after `WRITE_FAILED` reuses the same idempotency key. Repeating persistence after success does not create a second provider write in the reference model.

## Scope boundary

This is a synthetic in-memory model. It does not establish production provider semantics, crash consistency, distributed transaction guarantees, or a host/runtime memory lifecycle callback. Those remain separate research questions.
