# Research lifecycle

Every experiment starts from an explicit GitHub Issue and ends in an explicit disposition.

```text
Issue
→ experiment design
→ commit / PR
→ execution
→ evidence
→ verification
→ receipt
→ ACCEPTED | REJECTED | INCONCLUSIVE
```

Rules:

1. Commits advancing an open research question reference that Issue with `refs #N`.
2. Workflow success is execution evidence only.
3. Verification must test the declared postcondition independently when possible.
4. Receipts record exact source revision, runtime identity when observable, measured outputs, and epistemic boundary.
5. Negative results are retained; they are not rewritten into success narratives.
6. Memory/search evidence never silently becomes authority for destructive mutation or current-state claims.
7. Private correspondence and private memory contents stay outside this public control plane.
