from pathlib import Path


def test_voice_engine_has_probe_based_selection():
    source = Path('ai/voice.py').read_text(encoding='utf-8')
    assert '_probe_device' in source
    assert '_select_best_microphone' in source
    assert 'AIOS_INPUT_DEVICE' in source
    assert 'get_default_input_device_info' in source


def test_voice_engine_uses_ascii_model_path():
    source = Path('ai/voice.py').read_text(encoding='utf-8')
    assert r'C:\AIOS\models\stt\vosk-model-small-en-us-0.15' in source


def test_voice_engine_resamples_to_vosk_rate():
    source = Path('ai/voice.py').read_text(encoding='utf-8')
    assert 'self._resample_mono' in source
    assert 'self.sample_rate = 16000' in source
