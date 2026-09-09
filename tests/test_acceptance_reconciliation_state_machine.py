import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIM = ROOT / 'experiments/003-acceptance-reconciliation/simulate.py'
spec = importlib.util.spec_from_file_location('acceptance_reconciliation', SIM)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class AcceptanceReconciliationStateMachineTest(unittest.TestCase):
    def test_happy_path_reaches_reconciled_and_activates_user_asserted_memory(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.start('tx-1', 'mem-1', 'USER_ASSERTED', 'idem-1', {'claim': 'x'})

        attempt = mod.validate(attempt)
        attempt = mod.accept(attempt)
        attempt = mod.persist(attempt, provider)
        attempt = mod.verify_readback(attempt, provider)
        attempt = mod.reconcile(attempt, projection)

        self.assertEqual(attempt.transaction_state, mod.TransactionState.RECONCILED)
        self.assertEqual(attempt.semantic_state, mod.SemanticState.ACTIVE)
        self.assertEqual(provider.records['mem-1'], {'claim': 'x'})
        self.assertEqual(projection.records['mem-1'], {'claim': 'x'})

    def test_write_failure_does_not_claim_persistence_or_activation(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-2', 'mem-2', 'USER_ASSERTED', 'idem-2', {'claim': 'x'}
        )))

        attempt = mod.persist(attempt, provider, fail=True)

        self.assertEqual(attempt.transaction_state, mod.TransactionState.WRITE_FAILED)
        self.assertEqual(attempt.semantic_state, mod.SemanticState.PENDING)
        self.assertEqual(provider.records, {})
        self.assertEqual(projection.records, {})

    def test_readback_mismatch_keeps_persisted_record_unverified_and_pending(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-3', 'mem-3', 'USER_ASSERTED', 'idem-3', {'claim': 'x'}
        )))
        attempt = mod.persist(attempt, provider)

        attempt = mod.verify_readback(attempt, provider, mismatch=True)

        self.assertEqual(attempt.transaction_state, mod.TransactionState.READBACK_MISMATCH)
        self.assertEqual(attempt.semantic_state, mod.SemanticState.PENDING)
        self.assertEqual(provider.records['mem-3'], {'claim': 'x'})
        self.assertEqual(projection.records, {})

    def test_reconciliation_failure_preserves_verified_active_memory_but_not_projection(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-4', 'mem-4', 'USER_ASSERTED', 'idem-4', {'claim': 'x'}
        )))
        attempt = mod.persist(attempt, provider)
        attempt = mod.verify_readback(attempt, provider)

        attempt = mod.reconcile(attempt, projection, fail=True)

        self.assertEqual(attempt.transaction_state, mod.TransactionState.RECONCILIATION_PENDING)
        self.assertEqual(attempt.semantic_state, mod.SemanticState.ACTIVE)
        self.assertEqual(provider.records['mem-4'], {'claim': 'x'})
        self.assertEqual(projection.records, {})

    def test_assistant_derived_memory_stays_pending_even_after_full_materialization(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-5', 'mem-5', 'ASSISTANT_DERIVED', 'idem-5', {'claim': 'inference'}
        )))
        attempt = mod.persist(attempt, provider)
        attempt = mod.verify_readback(attempt, provider)
        attempt = mod.reconcile(attempt, projection)

        self.assertEqual(attempt.transaction_state, mod.TransactionState.RECONCILED)
        self.assertEqual(attempt.semantic_state, mod.SemanticState.PENDING)

    def test_reconcile_before_verified_readback_is_forbidden(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-6', 'mem-6', 'USER_ASSERTED', 'idem-6', {'claim': 'x'}
        )))
        attempt = mod.persist(attempt, provider)

        with self.assertRaises(mod.TransitionError):
            mod.reconcile(attempt, projection)

    def test_retry_after_write_failure_is_idempotent(self):
        provider = mod.ReferenceProvider()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-7', 'mem-7', 'USER_ASSERTED', 'idem-7', {'claim': 'x'}
        )))
        failed = mod.persist(attempt, provider, fail=True)

        retried = mod.persist(failed, provider)
        repeated = mod.persist(retried, provider)

        self.assertEqual(retried.transaction_state, mod.TransactionState.PERSISTED)
        self.assertEqual(repeated.transaction_state, mod.TransactionState.PERSISTED)
        self.assertEqual(provider.write_count, 1)
        self.assertEqual(provider.records, {'mem-7': {'claim': 'x'}})


if __name__ == '__main__':
    unittest.main()
