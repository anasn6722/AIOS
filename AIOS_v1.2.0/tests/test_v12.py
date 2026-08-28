from ai.voice import VoiceEngine
from ai.vision import VisionEngine
from ai.context import ContextEngine


def test_voice_status_is_safe_without_execution_access():
    status = VoiceEngine().status()
    assert set(status) == {"microphone_backend", "vosk", "model_path", "ready"}


def test_vision_engine_is_read_only_and_has_capture_path():
    engine = VisionEngine(ContextEngine())
    assert engine.capture_dir.name == "captures"
    assert engine.capture_dir.parent.name == ".aios"
