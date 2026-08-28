from __future__ import annotations

import json
import os
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - optional dependency in non-GUI test envs
    sd = None  # type: ignore[assignment]

try:
    from vosk import KaldiRecognizer, Model
except ImportError:  # pragma: no cover - optional dependency in non-GUI test envs
    KaldiRecognizer = None  # type: ignore[assignment]
    Model = None  # type: ignore[assignment]


@dataclass(frozen=True)
class VoiceResult:
    ok: bool
    message: str
    text: str = ""
    data: dict[str, Any] | None = None


class VoiceEngine:
    """Offline-first voice capture/transcription for the AIOS command center."""

    def __init__(self) -> None:
        self.model_path = self._find_model()
        self.sample_rate = 16000
        self.channels = 1

    def _find_model(self) -> Path | None:
        configured = os.environ.get("AIOS_VOSK_MODEL")
        candidates = []
        if configured:
            candidates.append(Path(configured).expanduser())
        candidates.extend(
            [
                Path.home() / ".aios" / "models" / "vosk-model-small-en-us-0.15",
                Path(__file__).resolve().parents[1] / "models" / "stt" / "vosk-model-small-en-us-0.15",
            ]
        )
        for candidate in candidates:
            if candidate.is_dir():
                return candidate
        return None

    def status(self) -> dict[str, Any]:
        return {
            "microphone_backend": sd is not None,
            "vosk": Model is not None and KaldiRecognizer is not None,
            "model_path": str(self.model_path) if self.model_path else None,
            "ready": sd is not None and Model is not None and self.model_path is not None,
        }

    def record_and_transcribe(self, seconds: int = 5) -> VoiceResult:
        status = self.status()
        if sd is None:
            return VoiceResult(False, "Voice capture unavailable. Install sounddevice.", data=status)
        if Model is None or KaldiRecognizer is None:
            return VoiceResult(False, "Local voice engine unavailable. Install vosk.", data=status)
        if self.model_path is None:
            return VoiceResult(
                False,
                "Vosk model not found. Set AIOS_VOSK_MODEL to a local model directory.",
                data=status,
            )

        seconds = max(1, min(int(seconds), 15))
        frames = int(self.sample_rate * seconds)
        try:
            recording = sd.rec(frames, samplerate=self.sample_rate, channels=self.channels, dtype="int16")
            sd.wait()
        except Exception as exc:  # backend errors vary by OS/audio driver
            return VoiceResult(False, f"Microphone capture failed: {exc}", data=status)

        recognizer = KaldiRecognizer(Model(str(self.model_path)), self.sample_rate)
        pcm = recording.reshape(-1).tobytes()
        if recognizer.AcceptWaveform(pcm):
            result = json.loads(recognizer.Result())
        else:
            result = json.loads(recognizer.FinalResult())
        text = str(result.get("text", "")).strip()
        if not text:
            return VoiceResult(False, "No speech was detected.", data=status)
        return VoiceResult(True, "Voice command transcribed.", text=text, data=status)
