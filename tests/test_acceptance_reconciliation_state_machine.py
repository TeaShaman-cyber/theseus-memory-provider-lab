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

    def test_nested_payload_is_snapshotted_across_transaction_and_provider_boundaries(self):
        provider = mod.ReferenceProvider()
        payload = {'claim': {'text': 'original'}}
        attempt = mod.accept(mod.validate(mod.start(
            'tx-8', 'mem-8', 'USER_ASSERTED', 'idem-8', payload
        )))

        payload['claim']['text'] = 'caller-mutated'
        self.assertEqual(attempt.payload, {'claim': {'text': 'original'}})

        attempt = mod.persist(attempt, provider)
        with self.assertRaises(TypeError):
            attempt.payload['claim']['text'] = 'attempt-mutated'

        self.assertEqual(provider.records['mem-8'], {'claim': {'text': 'original'}})
        self.assertEqual(
            provider.idempotency['idem-8'],
            ('mem-8', 'USER_ASSERTED', {'claim': {'text': 'original'}}),
        )

        verified = mod.verify_readback(attempt, provider)
        self.assertEqual(verified.transaction_state, mod.TransactionState.READBACK_VERIFIED)

    def test_reconciled_projection_is_snapshotted_from_attempt_payload(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-9', 'mem-9', 'USER_ASSERTED', 'idem-9', {'claim': {'text': 'original'}}
        )))
        attempt = mod.persist(attempt, provider)
        attempt = mod.verify_readback(attempt, provider)
        attempt = mod.reconcile(attempt, projection)

        with self.assertRaises(TypeError):
            attempt.payload['claim']['text'] = 'mutated-after-reconcile'

        self.assertEqual(
            projection.records['mem-9'],
            {'claim': {'text': 'original'}},
        )


    def test_reconcile_uses_payload_snapshot_that_passed_readback(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-10', 'mem-10', 'USER_ASSERTED', 'idem-10', {'claim': {'text': 'original'}}
        )))
        attempt = mod.persist(attempt, provider)
        attempt = mod.verify_readback(attempt, provider)

        provider.records['mem-10']['claim']['text'] = 'provider-mutated-after-readback'
        attempt = mod.reconcile(attempt, projection)

        self.assertEqual(attempt.transaction_state, mod.TransactionState.RECONCILED)
        self.assertEqual(
            provider.records['mem-10'],
            {'claim': {'text': 'provider-mutated-after-readback'}},
        )
        self.assertEqual(projection.records['mem-10'], {'claim': {'text': 'original'}})

    def test_verified_payload_snapshot_cannot_be_mutated_before_reconciliation(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-11', 'mem-11', 'USER_ASSERTED', 'idem-11', {'claim': {'text': 'original'}}
        )))
        attempt = mod.persist(attempt, provider)
        attempt = mod.verify_readback(attempt, provider)

        with self.assertRaises(TypeError):
            attempt.verified_payload['claim']['text'] = 'mutated-after-verification'

        attempt = mod.reconcile(attempt, projection)
        self.assertEqual(attempt.transaction_state, mod.TransactionState.RECONCILED)
        self.assertEqual(projection.records['mem-11'], {'claim': {'text': 'original'}})


    def test_start_rejects_non_json_payload_types(self):
        with self.assertRaises(mod.TransitionError):
            mod.start(
                'tx-12',
                'mem-12',
                'USER_ASSERTED',
                'idem-12',
                {'claim': ({'text': 'original'},)},
            )


    def test_accepted_payload_is_immutable_through_write_failure_and_retry(self):
        provider = mod.ReferenceProvider()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-13', 'mem-13', 'USER_ASSERTED', 'idem-13',
            {'claim': {'text': 'accepted'}}
        )))

        with self.assertRaises(TypeError):
            attempt.payload['claim']['text'] = 'mutated-after-accept'

        failed = mod.persist(attempt, provider, fail=True)
        with self.assertRaises(TypeError):
            failed.payload['claim']['text'] = 'mutated-after-write-failure'

        retried = mod.persist(failed, provider)
        self.assertEqual(provider.records['mem-13'], {'claim': {'text': 'accepted'}})
        self.assertEqual(retried.transaction_state, mod.TransactionState.PERSISTED)



    def test_json_comparison_distinguishes_boolean_from_number(self):
        provider = mod.ReferenceProvider()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-14', 'mem-14', 'USER_ASSERTED', 'idem-14', {'claim': True}
        )))
        persisted = mod.persist(attempt, provider)
        provider.records['mem-14'] = {'claim': 1}

        verified = mod.verify_readback(persisted, provider)
        self.assertEqual(verified.transaction_state, mod.TransactionState.READBACK_MISMATCH)

        other = mod.accept(mod.validate(mod.start(
            'tx-15', 'mem-14', 'USER_ASSERTED', 'idem-14', {'claim': 1}
        )))
        with self.assertRaises(mod.TransitionError):
            mod.persist(other, provider)


    def test_validate_freezes_candidate_and_rejects_non_json_mutation(self):
        attempt = mod.start(
            'tx-16', 'mem-16', 'USER_ASSERTED', 'idem-16',
            {'claim': {'text': 'candidate'}}
        )
        attempt.payload['claim']['extra'] = {'bad'}
        with self.assertRaises(mod.TransitionError):
            mod.validate(attempt)

        clean = mod.validate(mod.start(
            'tx-17', 'mem-17', 'USER_ASSERTED', 'idem-17',
            {'claim': {'text': 'validated'}}
        ))
        with self.assertRaises(TypeError):
            clean.payload['claim']['text'] = 'mutated-after-validate'

    def test_exact_json_comparison_rejects_non_string_provider_keys(self):
        provider = mod.ReferenceProvider()
        attempt = mod.accept(mod.validate(mod.start(
            'tx-18', 'mem-18', 'USER_ASSERTED', 'idem-18', {'1': 'v'}
        )))
        persisted = mod.persist(attempt, provider)
        provider.records['mem-18'] = {1: 'v'}

        verified = mod.verify_readback(persisted, provider)
        self.assertEqual(verified.transaction_state, mod.TransactionState.READBACK_MISMATCH)

        provider2 = mod.ReferenceProvider()
        provider2.idempotency['idem-19'] = ('mem-19', 'USER_ASSERTED', {1: 'v'})
        other = mod.accept(mod.validate(mod.start(
            'tx-19', 'mem-19', 'USER_ASSERTED', 'idem-19', {'1': 'v'}
        )))
        with self.assertRaises(mod.TransitionError):
            mod.persist(other, provider2)


    def test_idempotency_key_cannot_change_source_class(self):
        provider = mod.ReferenceProvider()
        derived = mod.accept(mod.validate(mod.start(
            'tx-20', 'mem-20', 'ASSISTANT_DERIVED', 'idem-20', {'claim': 'same'}
        )))
        mod.persist(derived, provider)

        asserted = mod.accept(mod.validate(mod.start(
            'tx-21', 'mem-20', 'USER_ASSERTED', 'idem-20', {'claim': 'same'}
        )))
        with self.assertRaises(mod.TransitionError):
            mod.persist(asserted, provider)

    def test_stale_verified_attempt_cannot_replace_newer_projection(self):
        provider = mod.ReferenceProvider()
        projection = mod.DerivedProjection()

        old = mod.accept(mod.validate(mod.start(
            'tx-22', 'mem-22', 'USER_ASSERTED', 'idem-22-old', {'claim': 'old'}
        )))
        old = mod.verify_readback(mod.persist(old, provider), provider)

        new = mod.accept(mod.validate(mod.start(
            'tx-23', 'mem-22', 'USER_ASSERTED', 'idem-22-new', {'claim': 'new'}
        )))
        new = mod.verify_readback(mod.persist(new, provider), provider)
        new = mod.reconcile(new, projection)
        self.assertEqual(projection.records['mem-22'], {'claim': 'new'})

        with self.assertRaises(mod.TransitionError):
            mod.reconcile(old, projection)
        self.assertEqual(projection.records['mem-22'], {'claim': 'new'})


    def test_readback_must_match_the_version_created_by_this_persist(self):
        provider = mod.ReferenceProvider()

        older = mod.accept(mod.validate(mod.start(
            'tx-24', 'mem-24', 'USER_ASSERTED', 'idem-24-old', {'claim': 'same'}
        )))
        older = mod.persist(older, provider)

        newer = mod.accept(mod.validate(mod.start(
            'tx-25', 'mem-24', 'ASSISTANT_DERIVED', 'idem-24-new', {'claim': 'same'}
        )))
        newer = mod.persist(newer, provider)

        self.assertEqual(provider.record_versions['mem-24'], 2)
        verified_older = mod.verify_readback(older, provider)
        self.assertEqual(
            verified_older.transaction_state,
            mod.TransactionState.READBACK_MISMATCH,
        )
        self.assertEqual(verified_older.semantic_state, mod.SemanticState.PENDING)
        self.assertIsNone(verified_older.verified_record_version)

        verified_newer = mod.verify_readback(newer, provider)
        self.assertEqual(
            verified_newer.transaction_state,
            mod.TransactionState.READBACK_VERIFIED,
        )
        self.assertEqual(verified_newer.verified_record_version, 2)



if __name__ == '__main__':
    unittest.main()
