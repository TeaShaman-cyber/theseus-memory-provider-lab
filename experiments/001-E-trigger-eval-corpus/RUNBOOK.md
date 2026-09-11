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
payload in current-chat context. It may contain only its verification or
application prompt plus the declared project/runtime environment.

`fresh session` removes current-chat conversational state; it does **not** imply
provider isolation. Project chat history, native ChatGPT memory, plugins/apps,
Skills, or other configured context routes may still explain a correct answer.
Every such route remains a recorded confounder unless independently excluded.

For a stimulus containing "для этого проекта", semantic scope must remain a
known project. Runs must use a unique disposable project identity so repeated
field tests cannot silently reuse an earlier project-memory fixture.

## Execution arms: do not confuse context isolation with provider isolation

The field test uses separate arms because current ChatGPT Projects can scope
project memory/context, while no documented per-project capability allowlist for
installed plugins/apps/skills is available on the tested surface. See #7.

```text
A. PRODUCTION_ROUTING
   ordinary ChatGPT environment
   no provider hints
   purpose: observe real route competition and automatic selection

B. CLEAN_PROJECT_ROUTING
   new disposable Project per run
   project-only memory
   zero files and no payload-bearing project instructions
   no provider hints
   purpose: reduce historical contamination while preserving realistic
            ButlerBrain-vs-native-project-memory competition

C. SOFT_PROVIDER_SCOPE
   new disposable Project per run
   project-only memory
   minimal Project Instructions request ButlerBrain as the only external
   persistent-memory provider
   purpose: provider lifecycle diagnostics under a soft policy boundary
   routing score: NON_ROUTING, because the router input was changed

D. HARD_PROVIDER_ISOLATION
   per-project capability allowlist/denylist or equivalent enforcement
   current disposition: BLOCKED on the documented ChatGPT Project surface
   until an enforceable boundary is observable
```

Recommended soft-scope Project Instructions for arm C:

```text
Experiment boundary:
- For persistent memory operations in this project, use ButlerBrain only.
- Do not substitute another external memory provider or continuity/search tool.
- If ButlerBrain cannot be used or attribution is not observable, report UNKNOWN.
- Do not treat an acknowledgement such as "remembered" as proof of persistence.
```

These instructions are a **behavioral request**, not a security/capability
boundary. Native project memory and hidden host behavior can still confound the
result. The user-observed Project Instructions UI limit (8,000 characters on the
tested account) is not treated as an OpenAI-documented invariant.

## Rerun isolation and unique canaries

A fixed semantic payload can be satisfied by a stale record from an earlier run.
Every strong-retain execution therefore needs both a disposable project and a
per-run canary.

Before the scored retain turn:

1. generate a unique `run_id` / project identifier;
2. for cases with synthetic objects, generate unique workflow/design canaries;
3. perform a **read-only forced provider preflight search** for the canary;
4. if the canary already exists, invalidate it and generate another;
5. label the preflight `NON_ROUTING` and exclude it from routing metrics.

After the retain turn, an explicit read-only provider search may be used to
verify persistence when the host does not expose an automatic readback. That
search is also `NON_ROUTING`. It can prove provider storage/readback when tied to
the unique canary, but cannot prove that ButlerBrain supplied a later ChatGPT
answer.

For `explicit-user-fact`, the disposable project's unique identifier is part of
the scope that a durable provider record must preserve. A generic old record such
as "reports should be short" is not sufficient evidence for the current run.

## Evidence and scoring vocabulary

Record at least:

```text
auto_route_selection:
  OBSERVED_YES | OBSERVED_NO | UNKNOWN

write_evidence:
  OBSERVED | NOT_OBSERVED | UNKNOWN

provider_postwrite_readback:
  PASS | FAIL | UNKNOWN

cross_session_readback:
  PASS | FAIL | UNKNOWN

application:
  PASS | FAIL | NON_DIAGNOSTIC | UNKNOWN

provider_attribution:
  CONFIRMED_BY_RETRIEVAL_TRACE | CONFOUNDED | UNKNOWN
```

`NOT_OBSERVED` is not proof that no write occurred when the host hides tool/Skill
execution. Use it only on an exposed surface where absence itself is observable;
otherwise use `UNKNOWN`.

For strong-retain cases, `provider_postwrite_readback = UNKNOWN` is an
**inconclusive lifecycle**, not `NOT_APPLICABLE`. A write may not be accepted as
verified persistence without readback evidence; this keeps
`write_without_readback_rate = 0` meaningful.

`CONFIRMED_BY_RETRIEVAL_TRACE` requires fresh-session retrieval-time evidence
that ButlerBrain supplied the relevant unique artifact/canary. An observed write
or an earlier post-write provider search is insufficient, because native project
memory or another mechanism could still supply the later answer. In the absence
of retrieval-time provider evidence, use `CONFOUNDED` or `UNKNOWN`.

Because hard provider isolation is currently `BLOCKED`, an isolated-environment
success is not available as an alternative path to confirmed attribution on this
surface.

## Strong-retain cases

Machine-readable fixtures and prompts are in `retain-protocol.json`.

### `explicit-user-fact`

Run in a newly created disposable Project whose unique project identifier is
recorded. Use project-only memory. Before the retain stimulus, confirm with a
read-only ButlerBrain search that no provider record containing that unique
project identifier exists.

After the frozen retain turn, a provider readback is `PASS` only if a ButlerBrain
result binds the formatting requirement to the current unique project scope. A
stale generic formatting preference is insufficient.

Cross-session verification asks for the saved report-format requirements without
restating them. Functional retrieval may still be explained by native project
memory; therefore it does not confirm ButlerBrain attribution by itself.

The downstream application uses a neutral synthetic reporting task and does not
say "use the saved requirements", "be short", or "include provenance". A matched
control Project with no retain stimulus receives the same neutral task. If both
arms naturally satisfy the formatting criteria, application is
`NON_DIAGNOSTIC`; only a retained-vs-control difference is evidence that the
retained rule changed behavior.

### `verified-external-effect`

The fixture supplies a **generated** per-run workflow ID and SHA before the frozen
stimulus. Fixed placeholder SHA values are invalid for execution. The later
provider readback and fresh-session verification must recover the exact run ID
and exact generated SHA plus the independent-verification provenance.

The application prompt asks for a journal record from the saved workflow result
without restating the outcome or SHA. Downgrading independently verified evidence
to an unverified assertion fails the original provenance invariant.

### `user-approved-decision`

The fixture establishes two synthetic candidate designs and an explicit proposed
choice, but does **not** claim user approval. Design B carries a generated unique
`design_canary`; the unchanged frozen stimulus supplies the approval event.

Provider readback and later verification must recover the exact current-run
canary, approved design, and rationale. A stale memory of an earlier Design B is
therefore unable to satisfy the current run. The application then chooses a next
step compatible with that retained design without restating its contents.

## Application-control rule

An application PASS is never provider attribution. For a behavioral property
that a model may produce by default (for example concise formatting), use a
matched control with the same application prompt but **without** the retain
stimulus.

```text
retained arm passes, control fails   -> application PASS (corroborative)
both arms pass                       -> NON_DIAGNOSTIC
retained arm fails                   -> application FAIL/UNKNOWN by evidence
```

The control establishes whether the retained state changed observable behavior;
it does not identify which memory source caused the change.

## Privacy and cleanup boundary

Use synthetic non-sensitive run IDs, project identifiers, design canaries, and
SHA values only. Do not place private conversation content, credentials, account
state, or real private operational artifacts into the public research log.

The currently observed ButlerBrain surface exposes save/search but no symmetric
thought-delete operation. Therefore this runbook makes no cleanup claim. A test
write is considered persistent until deletion is both available and independently
verified. Unique per-run canaries and disposable Projects prevent old records
from being accepted as evidence for a new run; they do not delete provider state.

## Platform limitation discovered during methodology review

`PROJECT_CONTEXT_ISOLATION != PROVIDER_ISOLATION`.

OpenAI's documented Project surface provides project-memory controls and allows
connected apps in Projects, while plugin/app availability is documented through
account/workspace/role controls rather than a per-project capability allowlist.
Project Instructions can request a routing policy but cannot prove that disabled
capabilities were technically ineligible.

This limitation is tracked separately in #7 because it affects both ordinary
user control and reproducible plugin/app development. The requested product
capabilities are per-project plugin/app/skill scoping plus user-visible event-level
routing/tool provenance; no chain-of-thought exposure is required.

## Minimum execution record

For each retain run, preserve a sanitized record containing:

```text
case_id
run_id / unique canary
execution_arm
project identity and project-memory mode
fixture validity
pre-run provider canary search
host / model when observable
auto-route evidence
provider calls / receipts when exposed
post-write readback status
fresh-session readback status
retrieval-time provider evidence
application status and matched-control result
competing routes / confounders
final provider attribution
hard-invariant violations
```

Positive, negative, and inconclusive runs all remain part of the research record.
