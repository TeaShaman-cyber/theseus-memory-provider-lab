# 001-E live execution runbook

Status: `DRAFT / REVIEW REQUIRED`

This document is an **additive execution protocol** for the frozen `001-E`
corpus. It does not change `evals.json`, its expectations, or its hard metrics.
It exists because a retain stimulus such as "remember X" is not itself evidence
that X became durable memory or that a later action actually used that memory.

Related research: #5.

## Feynman reduction: what does "remember" mean here?

For this experiment, a successful retain lifecycle means more than an assistant
saying that it remembered something.

The smallest useful model is:

```text
known precondition / fixture
        -> frozen retain stimulus
        -> observable write evidence when exposed
        -> provider read-after-write when naturally exposed
        -> fresh-session retrieval without restating the payload
        -> a later action that depends on the retained fact/decision
```

Each arrow is scored separately. A plausible final answer cannot retroactively
prove an unobserved earlier write, and a write receipt cannot prove that a fresh
session can retrieve or apply the state.

## Why the extra verification stage is necessary

A same-turn acknowledgement such as "Запомнил" can be produced from the current
conversation alone. It therefore proves neither durable persistence nor future
retrieval.

Similarly, a fresh-session answer can be functionally correct for the wrong
reason: project instructions, ChatGPT memory, Session Search, another plugin, or
another provider may have supplied the same information. That is useful
production evidence, but it is not automatically ButlerBrain attribution.

The protocol therefore keeps five evidence dimensions separate:

```text
1. automatic routing / Skill selection
2. provider write evidence
3. provider immediate read-after-write evidence
4. cross-session retrieval
5. downstream application of the retained state
```

## Five-whys failure decomposition

When a retain case cannot be verified, do not collapse the failure into
"memory failed".

```text
Why was the later action wrong?
  -> Was the retained state unavailable in the fresh session?
Why was it unavailable?
  -> Was there an observed write for the frozen stimulus?
Why was there no observed write?
  -> Was the provider selected automatically, another route selected, or selection hidden?
Why is attribution uncertain?
  -> Did another memory/context source contain the same payload?
Why can the experiment not decide?
  -> Is the missing stage genuinely unobservable in the host/runtime?
```

Stop at the first unsupported claim and record `UNKNOWN` or `CONFOUNDED` rather
than inventing the missing lifecycle stage.

## Frozen-corpus rule

The original query text in `evals.json` is immutable for scored runs. Fixtures,
verification prompts, and application prompts live in `retain-protocol.json`
and are **not** replacements for frozen stimuli.

At run time, verify that each protocol `stimulus` exactly equals the corresponding
`evals.json` query before execution.

## Route contamination rule

A researcher-forced provider call during a routing-scored corpus turn invalidates
provider-routing attribution for that turn. Such diagnostics may still be
recorded, but must be labeled `NON_ROUTING` and excluded from routing metrics.

The same rule applies to explicit instructions such as "use ButlerBrain" or
"call the memory plugin". They change the router's input and therefore do not
measure automatic selection.

## Fresh-session boundary

A verification session must not contain the original retain stimulus or its
payload. It may contain only the verification/application prompt and ordinary
host/project context.

`fresh session` removes current-chat conversational state; it does **not** imply
that project instructions, ChatGPT memory, plugins, or other configured context
sources disappear. These sources must be reported as competing routes when they
can explain the result.

For a stimulus containing "для этого проекта", semantic scope must remain the
same project. If that project already contains the tested payload through another
source, provider attribution is `CONFOUNDED` unless independent provider evidence
resolves it.

## Evidence and scoring vocabulary

Record at least:

```text
auto_route_selection:
  OBSERVED_YES | OBSERVED_NO | UNKNOWN

write_evidence:
  OBSERVED | NOT_OBSERVED | UNKNOWN

provider_postwrite_readback:
  PASS | FAIL | UNKNOWN | NOT_APPLICABLE

cross_session_readback:
  PASS | FAIL | UNKNOWN

application:
  PASS | FAIL | UNKNOWN

provider_attribution:
  CONFIRMED | CONFOUNDED | UNKNOWN
```

`NOT_OBSERVED` is not equivalent to proof that no write occurred when the host
hides tool/Skill execution. Use it only for an exposed surface where the absence
itself is observable; otherwise use `UNKNOWN`.

A routing metric may count a provider hit/miss only when the relevant attribution
is observable enough for that metric. Functional success from a competing route
is recorded separately and must not be silently converted into a provider hit.

## Strong-retain cases

Machine-readable fixtures and prompts are in `retain-protocol.json`.

### `explicit-user-fact`

No semantic fixture is added before the frozen stimulus; the test runs in a fresh
chat whose project scope is known. After the retain turn, verification happens in
another fresh chat without restating "короткими" or "provenance".

The lifecycle is accepted only if the later session can retrieve the saved
requirement and then use it while producing an actual report. Correct formatting
alone is corroborative, not provider attribution, because project instructions or
another memory layer could independently cause the same style.

### `verified-external-effect`

The fixture supplies a unique synthetic workflow run ID and SHA before the frozen
stimulus. This makes "Workflow" and "remote SHA" refer to one deterministic test
object while preserving the frozen stimulus unchanged.

The later session must recover both the outcome and its independent-verification
provenance, then emit a one-line journal record from the retained result.
Downgrading an independently verified result to an unverified assertion fails the
original provenance invariant.

### `user-approved-decision`

The fixture establishes two synthetic candidate designs and an explicit proposed
choice, but does **not** claim that the user approved it. The unchanged frozen
stimulus supplies the approval event.

The later session must identify which design the user approved and the reason,
then select a next step compatible with that approved design. If the fixture does
not make "этот дизайн" unambiguous before the stimulus, mark the fixture invalid
and do not score the run.

## Privacy and cleanup boundary

Use synthetic non-sensitive run IDs and synthetic SHA values only. Do not place
private conversation content, credentials, account state, or real private
operational artifacts into the public research log.

The currently observed ButlerBrain surface exposes save/search but no symmetric
thought-delete operation. Therefore this runbook makes no cleanup claim. A test
write is considered persistent until deletion is both available and independently
verified.

## Minimum execution record

For each retain run, preserve a sanitized record containing:

```text
case_id
run_id
host / model when observable
fixture validity
auto-route evidence
provider calls / receipts when exposed
post-write readback status
fresh-session readback status
application status
competing routes / confounders
final provider attribution
hard-invariant violations
```

Positive, negative, and inconclusive runs all remain part of the research record.
