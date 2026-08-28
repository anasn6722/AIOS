from __future__ import annotations

import array
import os
from dataclasses import dataclass
from pathlib import Path
from difflib import SequenceMatcher
from typing import Any

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None  # type: ignore[assignment]

try:
    import pyaudio
except ImportError:  # pragma: no cover
    pyaudio = None  # type: ignore[assignment]

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover
    sd = None  # type: ignore[assignment]

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover
    WhisperModel = None  # type: ignore[assignment]

try:
    from vosk import KaldiRecognizer, Model
except ImportError:  # pragma: no cover
    KaldiRecognizer = None  # type: ignore[assignment]
    Model = None  # type: ignore[assignment]


@dataclass(frozen=True)
class VoiceResult:
    ok: bool
    message: str
    text: str = ""
    data: dict[str, Any] | None = None


class VoiceEngine:
    """Offline-first Windows voice input.

    Primary recognizer: faster-whisper base.en on CPU/int8.
    Fallback recognizer: Vosk small English model.
    Audio capture: PyAudio first, sounddevice second.
    """

    SAMPLE_RATE = 16000
    CHUNK = 1024
    WHISPER_MODEL = os.environ.get("AIOS_WHISPER_MODEL", "base.en").strip() or "base.en"
    WHISPER_CACHE = Path(r"C:\AIOS\models\whisper")
    VOSK_MODEL_NAME = "vosk-model-small-en-us-0.15"
    VOSK_MODEL_PATH = Path(r"C:\AIOS\models\stt\vosk-model-small-en-us-0.15")

    COMMAND_PHRASES = [
        "open notepad", "open chrome", "open calculator", "open vscode",
        "open vs code", "open visual studio code", "open task manager",
        "open downloads", "open file manager", "open apps", "open dot",
        "show desktop", "system status", "aios health", "system health",
        "show aios health", "show service health", "show my context",
        "what is my current context", "what app am i using",
        "what is the active app", "show recent commands", "what did i just do",
        "show workspaces", "switch to coding", "switch to study",
        "switch to business", "find pdf", "find university pdf",
        "find my university documents",
    ]

    def __init__(self) -> None:
        self.sample_rate = self.SAMPLE_RATE
        self.channels = 1
        self.chunk = self.CHUNK
        self.input_device_index: int | None = None
        self.input_device_name: str | None = None
        self.input_host_api: str | None = None
        self.capture_rate = self.SAMPLE_RATE
        self.capture_channels = 1
        self.last_peak = 0
        self.last_rms = 0
        self.last_backend_error = ""
        self._device_selection_error = ""
        self._configured_device_error = ""
        self._backend: str | None = None
        self._whisper = None
        self._vosk = None
        self.vosk_model_path = self._find_vosk_model()
        self._select_best_microphone()
        self._update_backend_status()

    # ---------- model discovery ----------
    def _find_vosk_model(self) -> Path | None:
        configured = os.environ.get("AIOS_VOSK_MODEL", "").strip()
        candidates = [Path(configured)] if configured else []
        candidates += [
            self.VOSK_MODEL_PATH,
            Path.home() / ".aios" / "models" / "stt" / self.VOSK_MODEL_NAME,
            Path(__file__).resolve().parents[1] / "models" / "stt" / self.VOSK_MODEL_NAME,
        ]
        for path in candidates:
            if path and all((path / d).is_dir() for d in ("am", "conf", "graph", "ivector")):
                return path
        return None

    def _whisper_ready(self) -> bool:
        return WhisperModel is not None and np is not None

    def _load_whisper(self):
        if self._whisper is not None:
            return self._whisper
        if not self._whisper_ready():
            raise RuntimeError("faster-whisper and NumPy are not installed")
        self.WHISPER_CACHE.mkdir(parents=True, exist_ok=True)
        cpu_threads = max(2, min(6, (os.cpu_count() or 4) - 1))
        self._whisper = WhisperModel(
            self.WHISPER_MODEL,
            device="cpu",
            compute_type="int8",
            cpu_threads=cpu_threads,
            num_workers=1,
            download_root=str(self.WHISPER_CACHE),
        )
        return self._whisper

    def _load_vosk(self):
        if self._vosk is not None:
            return self._vosk
        if Model is None or KaldiRecognizer is None:
            raise RuntimeError("Vosk is not installed")
        if self.vosk_model_path is None:
            raise RuntimeError("Vosk model is not configured")
        self._vosk = Model(str(self.vosk_model_path))
        return self._vosk

    # ---------- microphone selection ----------
    def _device_info(self, audio, idx: int) -> dict[str, Any]:
        info = audio.get_device_info_by_index(idx)
        host = ""
        try:
            host = str(audio.get_host_api_info_by_index(int(info.get("hostApi", 0))).get("name", ""))
        except Exception:
            pass
        return {
            "index": idx,
            "name": str(info.get("name", "")),
            "host_api": host,
            "rate": int(float(info.get("defaultSampleRate", 44100))),
            "channels": int(info.get("maxInputChannels", 0)),
        }

    def _probe_device(self, audio, idx: int) -> tuple[bool, dict[str, Any], str]:
        info = self._device_info(audio, idx)
        if info["channels"] <= 0:
            return False, info, "no input channels"
        rates = []
        for rate in (info["rate"], 48000, 44100, 16000):
            if rate > 0 and rate not in rates:
                rates.append(rate)
        last_error = ""
        for rate in rates:
            stream = None
            try:
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=rate,
                    input=True,
                    input_device_index=idx,
                    frames_per_buffer=self.chunk,
                )
                stream.read(self.chunk, exception_on_overflow=False)
                return True, {**info, "capture_rate": rate}, ""
            except Exception as exc:
                last_error = str(exc)
            finally:
                if stream is not None:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass
        return False, info, last_error or "device could not be opened"

    def _select_best_microphone(self) -> None:
        if pyaudio is None:
            return
        audio = pyaudio.PyAudio()
        try:
            configured = os.environ.get("AIOS_INPUT_DEVICE", "").strip()
            preferred: list[int] = []
            if configured.isdigit():
                preferred.append(int(configured))
            try:
                default_idx = int(audio.get_default_input_device_info()["index"])
                if default_idx not in preferred:
                    preferred.append(default_idx)
            except Exception:
                pass

            scored: list[tuple[int, int]] = []
            for idx in range(audio.get_device_count()):
                try:
                    info = self._device_info(audio, idx)
                except Exception:
                    continue
                if info["channels"] <= 0:
                    continue
                name, host = info["name"].lower(), info["host_api"].lower()
                score = 0
                if idx in preferred:
                    score += 1000 if idx == preferred[0] else 800
                if "microphone" in name:
                    score += 100
                if "array" in name:
                    score += 50
                if "smart sound" in name:
                    score += 20
                if "wasapi" in host:
                    score += 15
                if info["rate"] in (44100, 48000, 16000):
                    score += 5
                scored.append((score, idx))

            order = preferred + [idx for _, idx in sorted(scored, reverse=True) if idx not in preferred]
            failures = []
            for idx in order:
                ok, info, error = self._probe_device(audio, idx)
                if ok:
                    self.input_device_index = idx
                    self.input_device_name = info["name"]
                    self.input_host_api = info["host_api"]
                    self.capture_rate = int(info.get("capture_rate", info["rate"]))
                    self.capture_channels = 1
                    return
                failures.append(f"{idx}: {info['name']} — {error}")
            self._device_selection_error = " | ".join(failures[:8])
        finally:
            audio.terminate()

    def _update_backend_status(self) -> None:
        if self.input_device_index is not None and pyaudio is not None:
            self._backend = "pyaudio"
        elif sd is not None:
            try:
                sd.query_devices(kind="input")
                self._backend = "sounddevice"
            except Exception:
                self._backend = None

    # ---------- diagnostics ----------
    def status(self) -> dict[str, Any]:
        whisper_available = self._whisper_ready()
        vosk_available = Model is not None and KaldiRecognizer is not None and self.vosk_model_path is not None
        return {
            "microphone_backend": self._backend is not None,
            "whisper": whisper_available,
            "whisper_model": self.WHISPER_MODEL,
            "vosk": vosk_available,
            "model_path": str(self.vosk_model_path) if self.vosk_model_path else None,
            "ready": self._backend is not None and (whisper_available or vosk_available),
        }

    def diagnostics(self) -> dict[str, Any]:
        data = self.status()
        data.update({
            "backend": self._backend,
            "input_device_index": self.input_device_index,
            "input_device_name": self.input_device_name,
            "input_host_api": self.input_host_api,
            "capture_rate": self.capture_rate,
            "capture_channels": self.capture_channels,
            "sounddevice": sd is not None,
            "pyaudio": pyaudio is not None,
            "numpy": np is not None,
            "last_peak": self.last_peak,
            "last_rms": self.last_rms,
            "device_selection_error": self._device_selection_error or self._configured_device_error,
            "last_backend_error": self.last_backend_error,
        })
        return data

    # ---------- audio ----------
    @staticmethod
    def _rms_and_peak(pcm: bytes) -> tuple[int, int]:
        samples = array.array("h")
        samples.frombytes(pcm)
        if not samples:
            return 0, 0
        peak = max(abs(v) for v in samples)
        mean_sq = sum(int(v) * int(v) for v in samples) // len(samples)
        return int(mean_sq ** 0.5), peak

    def _resample(self, pcm: bytes, source_rate: int, channels: int) -> bytes:
        src = array.array("h")
        src.frombytes(pcm)
        if channels > 1:
            mono = array.array("h")
            for i in range(0, len(src), channels):
                group = src[i:i + channels]
                mono.append(sum(group) // len(group) if group else 0)
            src = mono
        if source_rate == self.sample_rate:
            return src.tobytes()
        if not src:
            return b""
        target_len = max(1, int(len(src) * self.sample_rate / source_rate))
        out = array.array("h")
        for i in range(target_len):
            pos = i * source_rate / self.sample_rate
            left = min(len(src) - 1, int(pos))
            right = min(len(src) - 1, left + 1)
            frac = pos - left
            out.append(int(src[left] * (1.0 - frac) + src[right] * frac))
        return out.tobytes()

    def _record_pyaudio(self, seconds: int) -> bytes:
        if pyaudio is None:
            raise RuntimeError("PyAudio is unavailable")
        audio = pyaudio.PyAudio()
        stream = None
        try:
            idx = self.input_device_index
            if idx is None:
                idx = int(audio.get_default_input_device_info()["index"])
            info = audio.get_device_info_by_index(idx)
            rate = int(self.capture_rate or float(info.get("defaultSampleRate", 44100)))
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=rate,
                input=True,
                input_device_index=idx,
                frames_per_buffer=self.chunk,
            )
            chunks = []
            count = max(1, int(rate / self.chunk * seconds))
            for _ in range(count):
                chunks.append(stream.read(self.chunk, exception_on_overflow=False))
            raw = b"".join(chunks)
            self.last_rms, self.last_peak = self._rms_and_peak(raw)
            return self._resample(raw, rate, 1)
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            audio.terminate()

    def _record_sounddevice(self, seconds: int) -> bytes:
        if sd is None or np is None:
            raise RuntimeError("sounddevice or NumPy is unavailable")
        info = sd.query_devices(kind="input")
        rate = int(float(info.get("default_samplerate", 44100)))
        recording = sd.rec(int(rate * seconds), samplerate=rate, channels=1, dtype="int16")
        sd.wait()
        raw = recording.reshape(-1).tobytes()
        self.last_rms, self.last_peak = self._rms_and_peak(raw)
        return self._resample(raw, rate, 1)

    # ---------- recognition ----------
    @staticmethod
    def _normalize(text: str) -> str:
        text = " ".join(text.lower().strip().split())
        replacements = {
            "vs code": "vscode",
            "visual studio code": "vscode",
            "visual studio": "vscode",
            "google chrome": "chrome",
            "chrome browser": "chrome",
            "note pad": "notepad",
            "notepad and": "notepad",
            "chrome and": "chrome",
            "chromed": "chrome",
            "task manager and": "task manager",
            "file manager and": "file manager",
            "open dot": "open .",
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        for suffix in (" and", " please", " now", " for me"):
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()
        return text

    def _snap_to_command(self, text: str) -> str:
        text = self._normalize(text)
        if not text:
            return ""
        if text in self.COMMAND_PHRASES:
            return text
        best = ""
        best_score = 0.0
        for phrase in self.COMMAND_PHRASES:
            score = SequenceMatcher(None, text, phrase).ratio()
            if score > best_score:
                best_score, best = score, phrase
        # Only snap reasonably close results. This is intentionally not used
        # for arbitrary speech; the action policy remains the final guard.
        return best if best_score >= 0.72 else text

    def _transcribe_whisper(self, pcm: bytes) -> str:
        model = self._load_whisper()
        audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
        if audio.size == 0:
            return ""
        prompt = ", ".join(self.COMMAND_PHRASES)
        segments, _ = model.transcribe(
            audio,
            language="en",
            task="transcribe",
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=False,
            initial_prompt=prompt,
            hotwords=prompt,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 350},
            without_timestamps=True,
        )
        text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        return self._snap_to_command(text)

    def _transcribe_vosk(self, pcm: bytes) -> str:
        model = self._load_vosk()
        recognizer = KaldiRecognizer(model, self.sample_rate)
        recognizer.AcceptWaveform(pcm)
        import json
        result = json.loads(recognizer.FinalResult())
        return self._snap_to_command(str(result.get("text", "")))

    # ---------- public ----------
    def record_and_transcribe(self, seconds: int = 5) -> VoiceResult:
        seconds = max(3, min(int(seconds), 10))
        if self._backend is None:
            return VoiceResult(False, "No usable Windows microphone backend is available.", data=self.diagnostics())
        if not self._whisper_ready() and self.vosk_model_path is None:
            return VoiceResult(False, "No offline speech recognizer is installed/configured. Install faster-whisper or configure Vosk.", data=self.diagnostics())

        errors = []
        for backend in (["pyaudio", "sounddevice"] if pyaudio is not None else ["sounddevice"]):
            try:
                pcm = self._record_pyaudio(seconds) if backend == "pyaudio" else self._record_sounddevice(seconds)
                if self.last_rms < 20 and self.last_peak < 70:
                    errors.append(f"{backend}: microphone signal is too quiet (RMS={self.last_rms}, peak={self.last_peak})")
                    continue
                # Whisper is the primary recognizer because it is materially
                # more robust than the small Vosk model for natural speech.
                if self._whisper_ready():
                    text = self._transcribe_whisper(pcm)
                    if text:
                        self._backend = "faster-whisper"
                        return VoiceResult(True, "Voice command transcribed with Whisper.", text=text, data=self.diagnostics())
                if self.vosk_model_path is not None:
                    text = self._transcribe_vosk(pcm)
                    if text:
                        self._backend = "vosk"
                        return VoiceResult(True, "Voice command transcribed with Vosk fallback.", text=text, data=self.diagnostics())
                errors.append(f"{backend}: speech was not recognized (RMS={self.last_rms}, peak={self.last_peak})")
            except Exception as exc:
                self.last_backend_error = str(exc)
                errors.append(f"{backend}: {exc}")

        return VoiceResult(False, "Voice input failed. " + " | ".join(errors), data=self.diagnostics())
