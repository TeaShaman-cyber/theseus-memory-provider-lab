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

## Black-box engineering contract

The host router, native memory, Skill selection, and provider internals are treated
as a **black box** unless a stage is directly exposed by the tested surface. The
method therefore scores observable input/output relations, not guessed internal
mechanisms.

Feynman rule: every scored claim must be restatable as one simple observation,
for example: `the fresh-session provider trace returned proposition P`. Claims
such as `the router preferred ButlerBrain` are invalid unless the corresponding
selection evidence is actually exposed.

Five-Whys rule: when two hidden mechanisms can explain the same observation, keep
drilling only while another observable discriminator exists. If no discriminator
is available, stop with `CONFOUNDED` or `UNKNOWN`. Do not resolve observationally
equivalent explanations by plausibility.

This yields the central black-box invariant:

```text
observable provider retrieval of P
        !=
proof that hidden host logic chose P for the final answer
```

Provider retrieval, final-answer correctness, and causal source attribution are
therefore recorded separately.

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
   lifecycle scoring: INELIGIBLE; this arm is routing-only because ambient
                      project/history state is intentionally uncontrolled

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

1. generate a unique `run_id` / provider-visible scope marker;
2. for cases with synthetic objects, generate unique workflow/design canaries;
3. in a **separate diagnostic session**, perform a read-only forced provider
   preflight search for the canary/marker;
4. if the canary is returned, invalidate it and generate another; a search miss is
   only `NOT_FOUND_BY_THIS_QUERY`, never proof of global absence;
5. close the diagnostic session and start a **fresh routing conversation** before
   the fixture/stimulus;
6. label the preflight `NON_ROUTING` and exclude it from routing metrics.

After the retain turn, a researcher-forced read-only provider search may be used
as a **diagnostic persistence probe**. It is always `NON_ROUTING` and must be
recorded separately from `provider_postwrite_readback`. A forced diagnostic can
show that the provider can retrieve a proposition, but it cannot satisfy the
frozen automatic `READBACK` expectation or preserve the hard
`write_without_readback_rate = 0` metric. If automatic post-write readback is not
observable, that stage remains `UNKNOWN` and the strong-retain lifecycle is
inconclusive.

A canary is only a run discriminator, not the retained fact itself. Any provider
readback or fresh-session retrieval evidence used for scoring must contain the
**complete retained proposition** introduced by the scored turn, plus required
provenance, and bind it to the current run marker when one exists. Returning only
a canary or fixture content is insufficient.

## Evidence and scoring vocabulary

Record at least:

```text
auto_route_selection:
  OBSERVED_YES | OBSERVED_NO | UNKNOWN

write_evidence:
  OBSERVED | NOT_OBSERVED | UNKNOWN

provider_postwrite_readback:
  PASS | FAIL | UNKNOWN

diagnostic_persistence_probe:
  FOUND_COMPLETE_PROPOSITION | NOT_FOUND | UNKNOWN | NOT_RUN

cross_session_readback:
  PASS | FAIL | UNKNOWN

provider_retrieval_evidence:
  COMPLETE_PROPOSITION | PARTIAL_OR_FIXTURE_ONLY | UNKNOWN

final_answer_source_attribution:
  CONFOUNDED | UNKNOWN

application_functional_result:
  PASS | FAIL | UNKNOWN

application_memory_effect_evidence:
  NON_DIAGNOSTIC | INCONCLUSIVE_SINGLE_PAIR | NOT_RUN
```

`NOT_OBSERVED` is not proof that no write occurred when the host hides tool/Skill
execution. Use it only on an exposed surface where absence itself is observable;
otherwise use `UNKNOWN`.

For strong-retain cases, `provider_postwrite_readback = UNKNOWN` is an
**inconclusive lifecycle**, not `NOT_APPLICABLE`. A write may not be accepted as
verified persistence without readback evidence; this keeps
`write_without_readback_rate = 0` meaningful. A scored readback additionally
requires an observable provider **read operation distinct from the write/save**.
A save response that merely echoes submitted content is not read-after-write. The
read must return persisted record identity and/or stored content distinguishable
from the write input; otherwise readback remains `UNKNOWN`.

`provider_retrieval_evidence = COMPLETE_PROPOSITION` requires fresh-session
retrieval-time ButlerBrain evidence containing the complete retained proposition
and its required provenance, bound to the current run marker where applicable.
The evidence must come from an observable provider **read/search operation**
distinct from any fresh-session write/save. The returned persisted record/content
itself must contain the complete proposition and run marker/provenance and be
distinguishable from the retrieval request input. Request arguments, trace text,
provider echoes, or a newly created write result cannot establish retrieval because
hidden host context may already have placed the proposition into the request. A canary alone, fixture-only
content, an observed write, or an earlier forced provider search is insufficient.

Under the current black-box surface, observing a complete ButlerBrain retrieval
still does not prove that hidden host logic used that result rather than an
observationally equivalent native/project source in the final answer. Therefore
`final_answer_source_attribution` has no `CONFIRMED` state in this protocol. Hard
provider isolation or explicit host contribution telemetry would be required to
add one.

Because hard provider isolation is currently `BLOCKED`, provider retrieval can be
observed and scored while final-answer causal attribution remains `CONFOUNDED` or
`UNKNOWN`.

## Strong-retain cases

Machine-readable fixtures and prompts are in `retain-protocol.json`.

### `explicit-user-fact`

Run in a newly created disposable Project with project-only memory. The project
UI title is **not** assumed to be visible to ButlerBrain. Instead, a preceding
synthetic fixture turn supplies a unique provider-visible `scope_marker` and
explicitly states that it is only a test-scope identifier, not a formatting
requirement. Preflight search for that marker runs in a separate diagnostic
session before the routing conversation.

After the frozen retain turn, automatic provider readback is `PASS` only if an
observable provider **read operation distinct from the save/write** returns a
persisted record/content containing the complete formatting proposition (`short`
+ `provenance`) bound to the current `scope_marker`. A save-response echo, stale
generic formatting preference, the scope marker alone, or a later forced
diagnostic search cannot satisfy automatic readback.

Cross-session verification asks for the saved report-format requirements without
restating them. Functional retrieval may still be explained by native project
memory; therefore it does not confirm ButlerBrain attribution by itself.

The downstream application uses a neutral synthetic reporting task and does not
say "use the saved requirements", "be short", or "include provenance". A matched
control Project with no retain stimulus receives the same neutral task. A single
retained/control pair may record functional PASS/FAIL, but it is **not** causal
evidence that memory changed behavior: model variation can produce the same
difference by chance. One pair is therefore `INCONCLUSIVE_SINGLE_PAIR`; if both
arms naturally satisfy the criteria it is `NON_DIAGNOSTIC`. Repeated or
counterbalanced trials require a separately declared sampling/decision rule and
are outside this minimal field-test slice.

### `verified-external-effect`

The fixture supplies a **generated** per-run workflow ID and SHA before the frozen
stimulus. Fixed placeholder SHA values are invalid for execution. Because the
fixture itself already contains those canaries and remote-SHA provenance, neither
canary proves that the scored retain turn was stored. Automatic provider readback
and fresh-session provider retrieval evidence must also contain the proposition
introduced only by the frozen turn: **the workflow completed successfully**, plus
the independent-verification provenance.

The application prompt asks for a journal record from the saved workflow result
without restating the outcome or SHA. Functional PASS requires the journal line
to recover **the successful workflow outcome itself**, not merely the fixture's
run ID, SHA, and verification provenance. Downgrading independently verified
evidence to an unverified assertion fails the original provenance invariant.

### `user-approved-decision`

The fixture establishes two synthetic candidate designs and an explicit proposed
choice, but does **not** claim user approval. Design B carries a generated unique
`design_canary`; the unchanged frozen stimulus supplies the approval event.

Provider readback and later verification must recover the exact current-run
canary, the proposition introduced only by the frozen turn (**user approved
Design B for continued use**), and the rationale. The canary/rationale already
exist in the fixture and cannot by themselves prove retention of the approval
event. The application prompt must **not presuppose approval or even that work may
continue**. It asks whether the latest synthetic choice permits continuation; the
response itself must recover the user-approved Design B event before functional
PASS. Merely producing a step compatible with fixture-proposed Design B is
fixture-only evidence.

## Application-control rule

Application correctness and evidence of a memory effect are separate black-box
observations. For a behavioral property that a model may produce by default (for
example concise formatting), use a matched control with the same application
prompt but **without** the retain stimulus.

```text
retained arm functionally passes    -> application_functional_result = PASS
retained arm functionally fails     -> application_functional_result = FAIL/UNKNOWN
both arms pass                       -> memory_effect = NON_DIAGNOSTIC
single pair differs                 -> memory_effect = INCONCLUSIVE_SINGLE_PAIR
```

A single matched pair does not establish causality. Repeated/counterbalanced
trials may later estimate an effect, but require a predeclared sampling rule. The
control never identifies which memory source caused an observed difference.

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
pre-run provider canary search and diagnostic-session identity
host / model when observable
auto-route evidence
provider calls / receipts when exposed
automatic post-write readback status
forced diagnostic persistence-probe status
fresh-session functional readback status
retrieval-time provider proposition evidence
application functional result and matched-control disposition
competing routes / confounders
final-answer source attribution (`CONFOUNDED` / `UNKNOWN`)
hard-invariant violations
```

Positive, negative, and inconclusive runs all remain part of the research record.
