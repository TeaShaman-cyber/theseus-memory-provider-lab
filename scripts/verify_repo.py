#!/usr/bin/env python3
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
REQUIRED = [
    'README.md',
    'docs/architecture.md',
    'docs/research-lifecycle.md',
    'docs/wiki-bootstrap.md',
    'experiments/001-A-trigger-contract/README.md',
    'experiments/001-B-retain-transaction-semantics/simulate.py',
    'experiments/001-D-provider-adapter-fit/provider-contract-v0.md',
    'experiments/001-E-trigger-eval-corpus/evals.json',
    'tests/test_public_contract.py',
    'tests/test_retain_semantics.py',
    '.github/workflows/docs-check.yml',
]

PROHIBITED = re.compile(
    r'@gmail\.|permissions_current_account|Allow all actions|gh[opusr]_[A-Za-z0-9]{12,}|sk-[A-Za-z0-9_-]{12,}|poklad',
    re.IGNORECASE,
)


def fail(message: str) -> None:
    print(f'VERIFY FAIL: {message}', file=sys.stderr)
    raise SystemExit(1)


for rel in REQUIRED:
    if not (ROOT / rel).is_file():
        fail(f'missing required file: {rel}')

readme = (ROOT / 'README.md').read_text()
for token in [
    'https://github.com/TeaShaman-cyber/theseus-research',
    'does not define the Theseus program contract',
    'Wiki: ENABLED / MANUAL_FIRST_PAGE_REQUIRED',
    'Create the first page',
]:
    if token not in readme:
        fail(f'README missing contract marker: {token}')

receipts = sorted((ROOT / 'receipts').glob('*.json'))
if len(receipts) < 6:
    fail(f'expected at least 6 receipts, found {len(receipts)}')
for path in receipts:
    text = path.read_text()
    try:
        json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f'invalid JSON {path.name}: {exc}')
    if PROHIBITED.search(text):
        fail(f'prohibited private/account marker in receipt: {path.name}')

rows = json.loads((ROOT / 'experiments/001-E-trigger-eval-corpus/evals.json').read_text())
if not isinstance(rows, list) or len(rows) != 16:
    fail('trigger eval corpus must contain exactly 16 cases')

# Scan committed public text for credentials and direct personal-email markers.
text_suffixes = {'.md', '.json', '.py', '.yml', '.yaml'}
for path in ROOT.rglob('*'):
    if not path.is_file() or '.git' in path.parts or path.suffix not in text_suffixes:
        continue
    text = path.read_text(errors='replace')
    secret = re.search(r'gh[opusr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9._%+-]+@gmail\.com', text, re.IGNORECASE)
    if secret:
        fail(f'possible secret/private email marker in {path.relative_to(ROOT)}')

print(f'VERIFY PASS: required={len(REQUIRED)} receipts={len(receipts)} eval_cases={len(rows)}')
