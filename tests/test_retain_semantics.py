import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIM = ROOT / 'experiments/001-B-retain-transaction-semantics/simulate.py'
spec = importlib.util.spec_from_file_location('retain_simulate', SIM)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class RetainSemanticsTest(unittest.TestCase):
    def test_user_fact_survives_interrupted_final_safely(self):
        self.assertEqual(mod.stage('u1', 'USER_ASSERTED', True).state, mod.State.ACTIVE)

    def test_verified_external_effect_survives_interrupted_final_safely(self):
        self.assertEqual(mod.stage('e1', 'EXTERNAL_VERIFIED', True).state, mod.State.ACTIVE)

    def test_assistant_derived_never_promotes_at_stage(self):
        self.assertEqual(mod.stage('a1', 'ASSISTANT_DERIVED', True).state, mod.State.PENDING)

    def test_pending_only_confirms_with_later_visible_evidence(self):
        c = mod.stage('a2', 'ASSISTANT_DERIVED', True)
        self.assertEqual(mod.reconcile(c, evidence_visible=False).state, mod.State.PENDING)
        self.assertEqual(mod.reconcile(c, evidence_visible=True).state, mod.State.CONFIRMED)

    def test_contradiction_abandons_pending_candidate(self):
        c = mod.stage('a3', 'ASSISTANT_DERIVED', True)
        self.assertEqual(mod.reconcile(c, evidence_visible=True, contradicted=True).state, mod.State.ABANDONED)

    def test_failed_readback_never_promotes_to_active(self):
        self.assertEqual(mod.stage('u2', 'USER_ASSERTED', False).state, mod.State.UNKNOWN)

    def test_inferred_preference_stays_pending(self):
        self.assertEqual(mod.stage('p1', 'INFERRED_PREFERENCE', True).state, mod.State.PENDING)


if __name__ == '__main__':
    unittest.main()
