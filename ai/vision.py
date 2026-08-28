from __future__ import annotations

import ctypes
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from PIL import ImageGrab
except ImportError:  # pragma: no cover
    ImageGrab = None

import psutil
from ai.context import ContextEngine


@dataclass(frozen=True)
class VisionResult:
    ok: bool
    message: str
    data: dict[str, Any]


class VisionEngine:
    """Read-only local desktop understanding for AIOS v1.3."""

    def __init__(self, context: ContextEngine) -> None:
        self.context = context
        self.capture_dir = Path.home() / ".aios" / "captures"

    def capture_screen(self) -> VisionResult:
        if ImageGrab is None:
            return VisionResult(False, "Screen capture unavailable. Install Pillow.", {})
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        target = self.capture_dir / f"screen_{stamp}.png"
        try:
            image = ImageGrab.grab(all_screens=True)
            image.save(target)
        except (OSError, ValueError) as exc:
            return VisionResult(False, f"Screen capture failed: {exc}", {})
        analysis = self.analyze_desktop(target)
        return VisionResult(
            analysis.ok,
            analysis.message,
            {"image": str(target), "width": image.width, "height": image.height, **analysis.data},
        )

    def _windows(self) -> list[dict[str, Any]]:
        if os.name != "nt":
            return []
        user32 = ctypes.windll.user32
        callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        found: list[dict[str, Any]] = []

        def callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            title = buffer.value.strip()
            if not title:
                return True
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = None
            try:
                process_name = psutil.Process(int(pid.value)).name()
            except (psutil.Error, OSError):
                pass
            found.append({
                "title": title,
                "pid": int(pid.value),
                "process": process_name,
                "minimized": bool(user32.IsIconic(hwnd)),
            })
            return True

        try:
            user32.EnumWindows(callback_type(callback), 0)
        except OSError:
            return []
        return found

    def _ocr_text(self, image_path: Path | None) -> str | None:
        if image_path is None:
            return None
        try:
            import pytesseract
            raw = pytesseract.image_to_string(str(image_path), config="--psm 6")
        except Exception:
            return None
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return "\n".join(lines)[:5000] or None

    def analyze_desktop(self, image_path: Path | None = None) -> VisionResult:
        snapshot = self.context.snapshot()
        active = snapshot.get("active_window") or {}
        windows = self._windows()
        visible = [item for item in windows if not item.get("minimized")]
        ocr = self._ocr_text(image_path)

        lines = ["Local desktop analysis complete."]
        if active.get("process") or active.get("title"):
            lines.append(
                f"Active: {active.get('process') or 'Unknown process'} — "
                f"{active.get('title') or 'Untitled window'}"
            )
        lines.append(f"Visible windows: {len(visible)}")
        lines.extend(
            f"• {item['title']} [{item.get('process') or 'unknown'}]"
            for item in visible[:10]
        )
        lines.append("OCR: text detected on screen." if ocr else "OCR: unavailable or no text detected.")

        return VisionResult(
            True,
            "Screen analyzed locally.",
            {
                "active_window": active.get("title"),
                "active_process": active.get("process"),
                "visible_window_count": len(visible),
                "visible_windows": visible[:20],
                "ocr_text": ocr,
                "summary": "\n".join(lines),
            },
        )
