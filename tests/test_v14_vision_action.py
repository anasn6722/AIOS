from core.actions import ActionRequest, RiskLevel
from ai.orchestrator import Orchestrator


def test_inspect_screen_ui_command_maps_to_action():
    request = Orchestrator().interpret("show ui controls")
    assert request is not None
    assert request.name == "inspect_ui"
    assert request.risk == RiskLevel.SAFE


def test_click_command_is_confirmation_gated():
    request = Orchestrator().interpret("click Save")
    assert request is not None
    assert request.name == "click_control"
    assert request.parameters["target"] == "Save"
    assert request.risk == RiskLevel.MEDIUM


def test_vision_engine_exposes_find_control():
    from ai.vision import VisionEngine
    assert hasattr(VisionEngine, "inspect_controls")
    assert hasattr(VisionEngine, "find_control")
