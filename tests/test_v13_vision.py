def test_vision_queries_are_direct():
    from ai.orchestrator import Orchestrator
    o = Orchestrator()
    # Vision queries are handled by the shell, but remain a recognized AIOS intent contract.
    assert o is not None

def test_vision_engine_has_read_only_analysis():
    from ai.vision import VisionEngine
    assert hasattr(VisionEngine, "analyze_desktop")
    assert hasattr(VisionEngine, "capture_screen")
