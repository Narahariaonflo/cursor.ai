"""Validate an accepted run and reserve its initial budget envelope."""

from __future__ import annotations

from domain.entities.analysis_run import AnalysisRun
from domain.exceptions.errors import ValidationError
from domain.value_objects.enums import RunState
from ports.outbound.cost_governor import CostGovernorPort
from ports.outbound.logger import StructuredLoggerPort
from ports.outbound.policy import TargetPolicyPort
from ports.outbound.repository import ScanRepositoryPort


_INITIAL_RESERVATION_ID = "initial-run-envelope"


class ValidateAnalysisRun:
    """Advance an accepted run through policy and budget validation."""

    def __init__(
        self,
        repository: ScanRepositoryPort,
        target_policy: TargetPolicyPort,
        cost_governor: CostGovernorPort,
        logger: StructuredLoggerPort,
    ) -> None:
        """Store injected policy, budget, persistence, and logging ports."""
        self._repository = repository
        self._target_policy = target_policy
        self._cost_governor = cost_governor
        self._logger = logger

    def execute(self, tenant_id: str, run_id: str) -> None:
        """Validate a run and leave it in PLANNING or FAILED."""
        run = self._repository.get_run(tenant_id, run_id)
        if run is None:
            raise ValidationError("run_id not found")
        run.transition_to(RunState.VALIDATING)

        policy = self._target_policy.evaluate(run.target_url.value)
        if not policy.allowed:
            run.set_failure(policy.reason or "target denied")
            self._repository.save_run(run)
            self._logger.error(
                "analysis_run.target_denied",
                self._context(run, policy_code=policy.code),
            )
            return

        budget = self._cost_governor.validate_preferences(
            run.preferences.max_pages,
            run.preferences.max_depth,
        )
        if not budget.allowed:
            run.set_failure(budget.reason or "requested limits are not allowed")
            self._repository.save_run(run)
            self._logger.error(
                "analysis_run.limit_denied",
                self._context(run, budget_code=budget.code),
            )
            return

        reservation = self._cost_governor.reserve(
            run_id=run.run_id,
            reservation_id=_INITIAL_RESERVATION_ID,
            amounts={"pages": float(run.preferences.max_pages)},
        )
        if not reservation.allowed:
            run.set_failure(reservation.reason or "initial budget reservation denied")
            self._repository.save_run(run)
            self._logger.error(
                "analysis_run.budget_denied",
                self._context(run, budget_code=reservation.code),
            )
            return

        run.transition_to(RunState.PLANNING)
        self._repository.save_run(run)
        self._logger.info("analysis_run.planning", self._context(run))

    @staticmethod
    def _context(run: AnalysisRun, **extra: object) -> dict[str, object]:
        """Build required correlation context without sensitive content."""
        return {
            "tenant_id": run.tenant_id,
            "scan_run_id": run.run_id,
            "state": run.state.value,
            **extra,
        }
