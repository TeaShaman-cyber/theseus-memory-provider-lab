from dataclasses import dataclass
from enum import Enum

class State(str, Enum):
    ACTIVE='ACTIVE'
    PENDING='PENDING'
    CONFIRMED='CONFIRMED'
    SUPERSEDED='SUPERSEDED'
    ABANDONED='ABANDONED'
    UNKNOWN='UNKNOWN'

ACTIVE_SOURCES={'USER_ASSERTED','EXTERNAL_VERIFIED','USER_APPROVED_DECISION'}
PENDING_SOURCES={'ASSISTANT_DERIVED','INFERRED_PREFERENCE'}

@dataclass(frozen=True)
class Candidate:
    txid: str
    source_class: str
    state: State


def stage(txid: str, source_class: str, readback_ok: bool) -> Candidate:
    if not readback_ok:
        return Candidate(txid, source_class, State.UNKNOWN)
    if source_class in ACTIVE_SOURCES:
        return Candidate(txid, source_class, State.ACTIVE)
    if source_class in PENDING_SOURCES:
        return Candidate(txid, source_class, State.PENDING)
    return Candidate(txid, source_class, State.UNKNOWN)


def reconcile(c: Candidate, *, evidence_visible: bool, contradicted: bool=False) -> Candidate:
    if c.state != State.PENDING:
        return c
    if contradicted:
        return Candidate(c.txid, c.source_class, State.ABANDONED)
    if evidence_visible:
        return Candidate(c.txid, c.source_class, State.CONFIRMED)
    return c
