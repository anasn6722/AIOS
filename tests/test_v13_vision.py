def test_vision_engine_api():
    from ai.vision import VisionEngine
    assert hasattr(VisionEngine, "capture_screen")
    assert hasattr(VisionEngine, "analyze_desktop")

def test_vision_shell_queries_present():
    from pathlib import Path
    s = Path("desktop/shell.py").read_text(encoding="utf-8")
    assert "what is on my screen" in s
    assert "analyze my screen" in s
