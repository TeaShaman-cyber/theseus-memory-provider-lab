from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from enum import Enum
from types import MappingProxyType


TRANSITION_TABLE_VERSION = '0.1'


class TransitionError(RuntimeError):
    pass


class SemanticState(str, Enum):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'


class TransactionState(str, Enum):
    PROPOSED = 'PROPOSED'
    VALIDATED = 'VALIDATED'
    ACCEPTED = 'ACCEPTED'
    PERSISTED = 'PERSISTED'
    READBACK_VERIFIED = 'READBACK_VERIFIED'
    RECONCILED = 'RECONCILED'
    WRITE_FAILED = 'WRITE_FAILED'
    READBACK_MISMATCH = 'READBACK_MISMATCH'
    RECONCILIATION_PENDING = 'RECONCILIATION_PENDING'


ACTIVE_AFTER_READBACK = {
    'USER_ASSERTED',
    'EXTERNAL_VERIFIED',
    'USER_APPROVED_DECISION',
}


@dataclass(frozen=True)
class Attempt:
    txid: str
    record_id: str
    source_class: str
    idempotency_key: str
    payload: dict
    semantic_state: SemanticState
    transaction_state: TransactionState
    verified_payload: Mapping | None = None


def _freeze_payload(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_payload(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_payload(item) for item in value)
    return deepcopy(value)


def _thaw_payload(value):
    if isinstance(value, Mapping):
        return {key: _thaw_payload(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_payload(item) for item in value]
    return deepcopy(value)


class ReferenceProvider:
    def __init__(self):
        self.records = {}
        self.idempotency = {}
        self.write_count = 0

    def write(self, attempt: Attempt):
        prior = self.idempotency.get(attempt.idempotency_key)
        candidate = (attempt.record_id, deepcopy(attempt.payload))
        if prior is not None:
            if prior != candidate:
                raise TransitionError('idempotency key reused for different payload')
            return
        self.records[attempt.record_id] = deepcopy(attempt.payload)
        self.idempotency[attempt.idempotency_key] = candidate
        self.write_count += 1


class DerivedProjection:
    def __init__(self):
        self.records = {}


TRANSITIONS = {
    (TransactionState.PROPOSED, 'validate'): TransactionState.VALIDATED,
    (TransactionState.VALIDATED, 'accept'): TransactionState.ACCEPTED,
    (TransactionState.ACCEPTED, 'persist'): TransactionState.PERSISTED,
    (TransactionState.WRITE_FAILED, 'persist'): TransactionState.PERSISTED,
    (TransactionState.PERSISTED, 'readback'): TransactionState.READBACK_VERIFIED,
    (TransactionState.READBACK_MISMATCH, 'readback'): TransactionState.READBACK_VERIFIED,
    (TransactionState.READBACK_VERIFIED, 'reconcile'): TransactionState.RECONCILED,
    (TransactionState.RECONCILIATION_PENDING, 'reconcile'): TransactionState.RECONCILED,
}


def start(txid: str, record_id: str, source_class: str, idempotency_key: str, payload: dict) -> Attempt:
    return Attempt(
        txid=txid,
        record_id=record_id,
        source_class=source_class,
        idempotency_key=idempotency_key,
        payload=deepcopy(payload),
        semantic_state=SemanticState.PENDING,
        transaction_state=TransactionState.PROPOSED,
    )


def _advance(attempt: Attempt, operation: str) -> Attempt:
    target = TRANSITIONS.get((attempt.transaction_state, operation))
    if target is None:
        raise TransitionError(f'{operation} forbidden from {attempt.transaction_state.value}')
    return replace(attempt, transaction_state=target)


def validate(attempt: Attempt) -> Attempt:
    return _advance(attempt, 'validate')


def accept(attempt: Attempt) -> Attempt:
    return _advance(attempt, 'accept')


def persist(attempt: Attempt, provider: ReferenceProvider, *, fail: bool = False) -> Attempt:
    if attempt.transaction_state == TransactionState.PERSISTED:
        return attempt
    if attempt.transaction_state not in {TransactionState.ACCEPTED, TransactionState.WRITE_FAILED}:
        raise TransitionError(f'persist forbidden from {attempt.transaction_state.value}')
    if fail:
        return replace(attempt, transaction_state=TransactionState.WRITE_FAILED)
    provider.write(attempt)
    return _advance(attempt, 'persist')


def verify_readback(
    attempt: Attempt,
    provider: ReferenceProvider,
    *,
    mismatch: bool = False,
) -> Attempt:
    if attempt.transaction_state not in {TransactionState.PERSISTED, TransactionState.READBACK_MISMATCH}:
        raise TransitionError(f'readback forbidden from {attempt.transaction_state.value}')
    observed = provider.records.get(attempt.record_id)
    if mismatch or observed != attempt.payload:
        return replace(attempt, transaction_state=TransactionState.READBACK_MISMATCH)
    verified = _advance(attempt, 'readback')
    semantic_state = (
        SemanticState.ACTIVE
        if attempt.source_class in ACTIVE_AFTER_READBACK
        else SemanticState.PENDING
    )
    return replace(
        verified,
        semantic_state=semantic_state,
        verified_payload=_freeze_payload(observed),
    )


def reconcile(
    attempt: Attempt,
    projection: DerivedProjection,
    *,
    fail: bool = False,
) -> Attempt:
    if attempt.transaction_state == TransactionState.RECONCILED:
        return attempt
    if attempt.transaction_state not in {
        TransactionState.READBACK_VERIFIED,
        TransactionState.RECONCILIATION_PENDING,
    }:
        raise TransitionError(f'reconcile forbidden from {attempt.transaction_state.value}')
    if fail:
        return replace(attempt, transaction_state=TransactionState.RECONCILIATION_PENDING)
    if attempt.verified_payload is None:
        raise TransitionError('reconcile missing verified payload snapshot')
    projection.records[attempt.record_id] = _thaw_payload(attempt.verified_payload)
    return _advance(attempt, 'reconcile')
