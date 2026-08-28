def test_whisper_dependency_and_audio_pipeline_source():
    from pathlib import Path
    source = Path("ai/voice.py").read_text(encoding="utf-8")
    assert "faster_whisper" in source
    assert "compute_type=\"int8\"" in source
    assert "language=\"en\"" in source

def test_vosk_is_fallback_not_only_recognizer():
    from pathlib import Path
    source = Path("ai/voice.py").read_text(encoding="utf-8")
    assert "_transcribe_whisper" in source
    assert "_transcribe_vosk" in source
