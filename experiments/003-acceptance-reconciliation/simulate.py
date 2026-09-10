import json
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from enum import Enum
from math import isfinite
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
    payload: Mapping
    semantic_state: SemanticState
    transaction_state: TransactionState
    persisted_record_version: int | None = None
    verified_payload: Mapping | None = None
    verified_record_version: int | None = None


def _is_json_value(value):
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return isfinite(value)
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_json_value(item)
            for key, item in value.items()
        )
    return False


def _json_equal(left, right):
    if not _is_json_value(left) or not _is_json_value(right):
        return False
    return json.dumps(
        left, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False
    ) == json.dumps(
        right, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False
    )


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
        self.idempotency_versions = {}
        self.record_versions = {}
        self.write_count = 0

    def write(self, attempt: Attempt):
        prior = self.idempotency.get(attempt.idempotency_key)
        payload = _thaw_payload(attempt.payload)
        candidate = (attempt.record_id, attempt.source_class, deepcopy(payload))
        if prior is not None:
            same_record = prior[0] == candidate[0]
            same_source_class = prior[1] == candidate[1]
            same_payload = _json_equal(prior[2], candidate[2])
            if not same_record or not same_source_class or not same_payload:
                raise TransitionError('idempotency key reused for different operation identity')
            return self.idempotency_versions[attempt.idempotency_key]
        version = self.record_versions.get(attempt.record_id, 0) + 1
        self.records[attempt.record_id] = deepcopy(payload)
        self.record_versions[attempt.record_id] = version
        self.idempotency[attempt.idempotency_key] = candidate
        self.idempotency_versions[attempt.idempotency_key] = version
        self.write_count += 1
        return version


class DerivedProjection:
    def __init__(self):
        self.records = {}
        self.record_versions = {}


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
    if not isinstance(payload, dict) or not _is_json_value(payload):
        raise TransitionError('payload must be a JSON-compatible object')
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
    if not isinstance(attempt.payload, dict) or not _is_json_value(attempt.payload):
        raise TransitionError('payload must remain a JSON-compatible object through validation')
    validated = _advance(attempt, 'validate')
    return replace(validated, payload=_freeze_payload(validated.payload))


def accept(attempt: Attempt) -> Attempt:
    return _advance(attempt, 'accept')


def persist(attempt: Attempt, provider: ReferenceProvider, *, fail: bool = False) -> Attempt:
    if attempt.transaction_state == TransactionState.PERSISTED:
        return attempt
    if attempt.transaction_state not in {TransactionState.ACCEPTED, TransactionState.WRITE_FAILED}:
        raise TransitionError(f'persist forbidden from {attempt.transaction_state.value}')
    if fail:
        return replace(attempt, transaction_state=TransactionState.WRITE_FAILED)
    persisted_record_version = provider.write(attempt)
    persisted = _advance(attempt, 'persist')
    return replace(persisted, persisted_record_version=persisted_record_version)


def verify_readback(
    attempt: Attempt,
    provider: ReferenceProvider,
    *,
    mismatch: bool = False,
) -> Attempt:
    if attempt.transaction_state not in {TransactionState.PERSISTED, TransactionState.READBACK_MISMATCH}:
        raise TransitionError(f'readback forbidden from {attempt.transaction_state.value}')
    observed = provider.records.get(attempt.record_id)
    observed_version = provider.record_versions.get(attempt.record_id)
    expected = _thaw_payload(attempt.payload)
    if (
        mismatch
        or observed is None
        or observed_version is None
        or attempt.persisted_record_version is None
        or observed_version != attempt.persisted_record_version
        or not _json_equal(observed, expected)
    ):
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
        verified_record_version=observed_version,
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
    if attempt.verified_payload is None or attempt.verified_record_version is None:
        raise TransitionError('reconcile missing verified payload snapshot or record version')
    candidate = _thaw_payload(attempt.verified_payload)
    current_version = projection.record_versions.get(attempt.record_id)
    if current_version is not None:
        if current_version > attempt.verified_record_version:
            raise TransitionError('stale reconciliation cannot replace newer projection')
        if current_version == attempt.verified_record_version:
            current = projection.records.get(attempt.record_id)
            if current is None or not _json_equal(current, candidate):
                raise TransitionError('projection version conflicts with verified payload')
            return _advance(attempt, 'reconcile')
    projection.records[attempt.record_id] = candidate
    projection.record_versions[attempt.record_id] = attempt.verified_record_version
    return _advance(attempt, 'reconcile')
