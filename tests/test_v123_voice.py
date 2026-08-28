from ai.voice import VoiceEngine


def test_normalize_common_small_model_slips():
    assert VoiceEngine._normalize_command("chrome and") == "chrome"
    assert VoiceEngine._normalize_command("chromed") == "chrome"
    assert VoiceEngine._normalize_command("not bad") == "notepad"
    assert VoiceEngine._normalize_command("note pad") == "notepad"
    assert VoiceEngine._normalize_command("vs code") == "vscode"


def test_known_voice_phrases_present():
    engine = VoiceEngine()
    assert "open notepad" in engine.command_phrases
    assert "open chrome" in engine.command_phrases
    assert "open vscode" in engine.command_phrases
    assert "system status" in engine.command_phrases
