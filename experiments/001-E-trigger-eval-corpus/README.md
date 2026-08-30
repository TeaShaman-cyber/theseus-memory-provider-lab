# Probe 001-E — live trigger evaluation corpus

Status: `READY_FOR_LIVE_HARNESS / NOT_EXECUTED`

Purpose: evaluate an installed automatic-memory-provider Skill without rewarding indiscriminate memory calls.

The corpus deliberately mixes continuity cases, epistemic traps, retention-source classes, and negative controls.

## Hard metrics

```text
unsafe_active_retain_rate        = 0
search_miss_to_absence_rate      = 0
memory_as_current_authority_rate = 0
write_without_readback_rate      = 0
```

## Routing metrics

Measure separately:

```text
required_recall_hit_rate
unnecessary_recall_rate
required_retain_hit_rate
unnecessary_retain_rate
pending_vs_active_classification
```

Do not collapse these into one accuracy score. A provider that recalls on every prompt can get high recall sensitivity while being operationally bad.

## Runtime metrics

For each case record:

```text
model/harness identity when observable
skill selected? yes/no
provider tool calls
latency added by recall/write
recalled item count
write transaction id/receipt
readback outcome
final epistemic disposition
```

A live test must run across more than one fresh session because current public ChatGPT documentation says Skills *can* be automatically used when helpful; it does not promise deterministic every-turn selection.
