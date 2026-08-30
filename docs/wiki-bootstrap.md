# Wiki bootstrap

GitHub Wiki has a one-time manual bootstrap boundary.

Enabling Wiki in repository settings is not sufficient evidence that the Git remote exists. Before the first page was created, this repository correctly recorded:

```text
Wiki: ENABLED / MANUAL_FIRST_PAGE_REQUIRED
```

## Manual initialization completed

A human created the initial `Home` page in the GitHub UI. After that action, the Wiki Git remote became observable:

```text
git ls-remote https://github.com/TeaShaman-cyber/theseus-memory-provider-lab.wiki.git
```

The remote was then cloned and seeded with the research navigation pages through the governed wrapper.

Current verified state:

```text
Wiki: WIKI_GIT_REMOTE_VERIFIED
branch: master
commit: 1e889df149c57e3c2b1e7ce3e8804c96f88046a2
```

Verified pages:

- `Home.md`
- `Terminology.md`
- `Research-Lifecycle.md`
- `Experiment-Traceability.md`
- `Memory-Provider-Contract.md`

## Ongoing maintenance

Subsequent Wiki maintenance uses:

```bash
/workspace/tools/wiki-push.sh /path/to/wiki-checkout
```

The wrapper performs a write preflight, push, and remote SHA readback. An independent readback should still be used for important structural changes.

Wiki is navigation. The main Git repository remains canonical for research contracts, experiments, receipts, tests, and version history.
