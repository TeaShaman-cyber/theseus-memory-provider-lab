# Theseus Memory Provider Lab

Theseus Memory Provider Lab is a public research line under the [Theseus public-interest research program](https://github.com/TeaShaman-cyber/theseus-research). This repository does not define the Theseus program contract.

Its purpose is to study automatic persistent-memory behavior around ChatGPT/Codex-style Skills and memory Apps: bounded recall, context injection, source-aware retain, exact persistence readback, lifecycle reconciliation, and the boundary between model-mediated automation and host-enforced callbacks.

## Research boundary

- A model-selected Skill is not assumed to be identical to a host-level `MemoryProvider`.
- Recalled memory is evidence, not current operational authority.
- Search miss means `UNKNOWN`, not absence, unless coverage is independently known complete.
- Negative and inconclusive results are first-class research outcomes.
- Public material may include public upstream SHAs, synthetic evals, provider interface observations, and sanitized receipts.
- Private correspondence, user conversation data, private memory contents, identity values, credentials, tokens, and account-specific permission settings are not published here.
- Public visibility is for research transparency. No open-source license is granted by this bootstrap.

## Research flow

```text
Issue
→ experiment
→ commit/PR
→ execution
→ evidence
→ verification
→ receipt
→ disposition
```

Commits advancing an open question use `refs #N`. `closes #N` / `fixes #N` are reserved for final disposition.

See [architecture](docs/architecture.md) and [research lifecycle](docs/research-lifecycle.md).

## Seed research question

Issue #1 asks whether a Skill plus a persistent-memory App can approximate an automatic memory provider safely enough for auto-recall and source-aware auto-retain, and which guarantees still require host/runtime lifecycle support.

The initial public probe set is:

- `001-A` — Skill/App trigger contract;
- `001-B` — source-aware retain transaction semantics;
- `001-C` — public ChatGPT hook-surface boundary;
- `001-D` — provider adapter fit and minimal provider API contract;
- `001-E` — falsifiable live-trigger evaluation corpus with negative controls.

## Initial working model

```text
user turn
   ↓
auto-selected memory Skill
   ↓
bounded recall from memory App
   ↓
small evidence working set
   ↓
substantive task
   ↓
source-aware durable delta
   ↓
write + exact readback where supported
```

The missing host-level pieces are investigated explicitly rather than assumed.

## Wiki bootstrap

**Current bootstrap status:**

```text
Wiki: WIKI_GIT_REMOTE_VERIFIED
```

GitHub Wiki required one manual initialization step: the first `Home` page had to be created in the GitHub UI before the `.wiki.git` remote existed. That one-time boundary is now complete.

Verified Wiki seed commit:

```text
1e889df149c57e3c2b1e7ce3e8804c96f88046a2
```

The Wiki now contains `Home`, `Terminology`, `Research-Lifecycle`, `Experiment-Traceability`, and `Memory-Provider-Contract`. Subsequent Wiki changes are managed through the governed Wiki wrapper and require remote SHA readback.

Wiki remains a human navigation surface; contracts, experiments, receipts, and executable checks remain canonical in the main repository.

See [Wiki bootstrap](docs/wiki-bootstrap.md).

## Verification

Run locally:

```bash
python3 scripts/verify_repo.py
python3 -m unittest discover -s tests -v
```

A green check proves only the repository contract and local semantic invariants encoded by those tests. It does not prove that ChatGPT will trigger a memory Skill deterministically or that a provider has production-safe lifecycle semantics.
