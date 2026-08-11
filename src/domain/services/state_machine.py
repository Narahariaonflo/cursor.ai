"""Analysis run state-transition rules."""

from __future__ import annotations

from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import RunState


_ALLOWED_TRANSITIONS: dict[RunState, frozenset[RunState]] = {
    RunState.ACCEPTED: frozenset({RunState.VALIDATING}),
    RunState.VALIDATING: frozenset({RunState.PLANNING, RunState.FAILED}),
    RunState.PLANNING: frozenset({RunState.RUNNING, RunState.FAILED}),
    RunState.RUNNING: frozenset({RunState.AGGREGATING, RunState.FAILED}),
    RunState.AGGREGATING: frozenset({RunState.RENDERING, RunState.FAILED}),
    RunState.RENDERING: frozenset(
        {RunState.COMPLETED, RunState.PARTIAL, RunState.FAILED},
    ),
    RunState.COMPLETED: frozenset(),
    RunState.PARTIAL: frozenset(),
    RunState.FAILED: frozenset(),
}


def validate_transition(current: RunState, target: RunState) -> None:
    """Reject lifecycle transitions not permitted by the approved state model."""
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise ValidationError(f"invalid run transition: {current.value} -> {target.value}")
