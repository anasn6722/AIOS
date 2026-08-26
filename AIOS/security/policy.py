from __future__ import annotations

from core.actions import ActionRequest, RiskLevel


class PolicyEngine:
    """Central gate between AI intent and executable system actions."""

    def requires_confirmation(self, request: ActionRequest) -> bool:
        return request.risk in {
            RiskLevel.MEDIUM,
            RiskLevel.HIGH,
            RiskLevel.CRITICAL,
        }

    def authorize(self, request: ActionRequest, confirmed: bool = False) -> bool:
        if request.risk in {RiskLevel.SAFE, RiskLevel.LOW}:
            return True
        return confirmed
