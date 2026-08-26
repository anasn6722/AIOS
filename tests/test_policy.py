from core.actions import ActionRequest, RiskLevel
from security.policy import PolicyEngine


def test_safe_action_does_not_require_confirmation() -> None:
    engine = PolicyEngine()
    request = ActionRequest("system_info", risk=RiskLevel.SAFE)
    assert engine.requires_confirmation(request) is False
    assert engine.authorize(request) is True


def test_medium_risk_requires_confirmation() -> None:
    engine = PolicyEngine()
    request = ActionRequest("example", risk=RiskLevel.MEDIUM)
    assert engine.requires_confirmation(request) is True
    assert engine.authorize(request) is False
    assert engine.authorize(request, confirmed=True) is True
