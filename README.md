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

## Wiki bootstrap — one manual GitHub step

**Current bootstrap status:**

```text
Wiki: ENABLED / MANUAL_FIRST_PAGE_REQUIRED
```

GitHub can report Wiki as enabled before the repository's `.wiki.git` remote exists. The first page must be created manually in the GitHub UI.

After this repository is created:

1. Open this repository on GitHub.
2. Open the **Wiki** tab.
3. Click **Create the first page**.
4. Create and save the initial `Home` page.
5. Only after that step should `theseus-memory-provider-lab.wiki.git` be expected to exist.

After the first page exists, subsequent Wiki pages can be managed and independently verified through Git. Wiki remains a human navigation surface; contracts, experiments, receipts, and executable checks remain canonical in the main repository.

See [Wiki bootstrap](docs/wiki-bootstrap.md).

## Verification

Run locally:

```bash
python3 scripts/verify_repo.py
python3 -m unittest discover -s tests -v
```

A green check proves only the repository contract and local semantic invariants encoded by those tests. It does not prove that ChatGPT will trigger a memory Skill deterministically or that a provider has production-safe lifecycle semantics.
