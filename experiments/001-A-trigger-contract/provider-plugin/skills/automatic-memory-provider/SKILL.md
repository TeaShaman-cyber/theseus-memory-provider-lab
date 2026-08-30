---
name: automatic-memory-provider
description: Use on every non-trivial user turn when prior user, project, relationship, decision, or workflow context could affect the response. Recall relevant persistent memory before substantive work. If durable new context emerges, stage a concise retention candidate before the final response. Skip greetings, acknowledgements, and clearly stateless tasks.
---

# Automatic Memory Provider

This skill approximates a persistent-memory provider using ChatGPT's automatic Skill routing plus the memory App shipped by the same plugin.

## Pre-answer recall

Before substantive reasoning, answering, or external action:

1. Search the provider for a small bounded set of memories relevant to the current user turn and unresolved referents.
2. Treat recalled items as evidence, not authority. A stored claim can be stale, contradicted, superseded, or wrong.
3. When the request depends on current operational truth, verify against the authoritative live source instead of trusting memory.
4. Inject only the smallest useful recalled working set into reasoning; do not dump the provider history into context.
5. A search miss means UNKNOWN, not absence, unless coverage is independently known to be complete.

## During the turn

Keep provider memory distinct from the current conversation and tool evidence. Prefer current verified observations over stored operational claims. Preserve provenance when recalled items materially affect the answer.

## Retention candidate

Before sending the final response, only when durable new information emerged:

1. Distill a compact delta rather than saving the whole transcript or assistant answer.
2. Prefer explicit user facts, durable preferences, decisions, verified outcomes, stable project state, and reusable lessons.
3. Do not persist secrets, transient tool output, speculative inference as fact, or duplicated recalled memory.
4. Stage the delta with provenance and an idempotency/turn identifier when the provider supports them.
5. Do not claim exact post-turn persistence unless a provider readback or later reconciliation observes it.

If no durable delta emerged, do not write memory merely because the skill ran.

## Lifecycle boundary

This is model-mediated automation. It is not a host-enforced pre-turn/post-turn callback. The host may auto-select this Skill when useful, but the Skill cannot prove that it ran on every turn or after the final assistant bytes were emitted.
