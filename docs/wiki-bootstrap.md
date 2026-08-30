# Wiki bootstrap

GitHub Wiki has a one-time manual bootstrap boundary.

Enabling Wiki in repository settings is not sufficient evidence that the Git remote exists. Before the first page is created, this repository records:

```text
Wiki: ENABLED / MANUAL_FIRST_PAGE_REQUIRED
```

## Required manual step

1. Open the repository on GitHub.
2. Open the **Wiki** tab.
3. Click **Create the first page**.
4. Create/save `Home`.

Only after that step should this probe succeed:

```bash
git ls-remote https://github.com/TeaShaman-cyber/theseus-memory-provider-lab.wiki.git
```

After the remote exists, subsequent Wiki maintenance may use the governed MarcoPolo wrapper:

```bash
/workspace/tools/wiki-push.sh /path/to/wiki-checkout
```

That wrapper performs a write preflight, push, and remote SHA readback. Wiki is navigation; the main Git repository remains canonical for research contracts and receipts.
