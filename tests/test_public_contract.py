import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PublicContractTest(unittest.TestCase):
    def test_required_public_tree_exists(self):
        required = [
            'README.md',
            'docs/architecture.md',
            'docs/research-lifecycle.md',
            'docs/wiki-bootstrap.md',
            'experiments/001-B-retain-transaction-semantics/simulate.py',
            'experiments/001-E-trigger-eval-corpus/evals.json',
            'scripts/verify_repo.py',
            '.github/workflows/docs-check.yml',
        ]
        for rel in required:
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_readme_declares_parent_and_verified_wiki_bootstrap(self):
        text = (ROOT / 'README.md').read_text()
        self.assertIn('https://github.com/TeaShaman-cyber/theseus-research', text)
        self.assertIn('Wiki: WIKI_GIT_REMOTE_VERIFIED', text)
        self.assertIn('1e889df149c57e3c2b1e7ce3e8804c96f88046a2', text)
        self.assertTrue((ROOT / 'receipts/001-F-wiki-bootstrap.json').is_file())
        self.assertIn('does not define the Theseus program contract', text)

    def test_public_receipts_are_json_and_private_markers_are_absent(self):
        receipt_dir = ROOT / 'receipts'
        files = sorted(receipt_dir.glob('*.json'))
        self.assertGreaterEqual(len(files), 6)
        prohibited = re.compile(
            r'@gmail\.|permissions_current_account|Allow all actions|gh[opusr]_[A-Za-z0-9]{12,}|sk-[A-Za-z0-9_-]{12,}|poklad',
            re.IGNORECASE,
        )
        for path in files:
            text = path.read_text()
            json.loads(text)
            self.assertIsNone(prohibited.search(text), path.name)

    def test_trigger_eval_corpus_has_sixteen_cases(self):
        rows = json.loads((ROOT / 'experiments/001-E-trigger-eval-corpus/evals.json').read_text())
        self.assertEqual(len(rows), 16)


if __name__ == '__main__':
    unittest.main()

class RepositoryHygieneTest(unittest.TestCase):
    def test_no_generated_python_cache_is_tracked(self):
        import subprocess
        tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
        bad = [p for p in tracked if '/__pycache__/' in f'/{p}' or p.endswith('.pyc')]
        self.assertEqual(bad, [])
