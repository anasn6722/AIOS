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
    """Local desktop understanding and UI-inspection layer.

    v1.4 adds Windows UI Automation inspection. It can identify visible UI
    controls and propose a click target, but execution remains behind the
    policy-controlled SystemAdapter.
    """

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

        analyzed = self.analyze_desktop(target)
        return VisionResult(
            analyzed.ok,
            analyzed.message,
            {"image": str(target), "width": image.width, "height": image.height, **analyzed.data},
        )

    def _foreground_hwnd(self) -> int | None:
        if os.name != "nt":
            return None
        try:
            hwnd = int(ctypes.windll.user32.GetForegroundWindow())
            return hwnd or None
        except (AttributeError, OSError):
            return None

    def inspect_controls(self, limit: int = 80) -> VisionResult:
        """Return visible UIA controls from the foreground Windows window."""
        if os.name != "nt":
            return VisionResult(False, "UI inspection is currently supported on Windows only.", {})
        try:
            from pywinauto import Desktop
        except ImportError:
            return VisionResult(False, "UI Automation unavailable. Install pywinauto.", {})

        hwnd = self._foreground_hwnd()
        if not hwnd:
            return VisionResult(False, "No foreground window is available.", {})

        try:
            window = Desktop(backend="uia").window(handle=hwnd)
            controls: list[dict[str, Any]] = []
            for element in window.descendants():
                try:
                    info = element.element_info
                    name = (element.window_text() or "").strip()
                    control_type = getattr(info, "control_type", None)
                    if not name and not control_type:
                        continue
                    rect = element.rectangle()
                    controls.append(
                        {
                            "name": name,
                            "control_type": control_type,
                            "automation_id": getattr(info, "automation_id", None),
                            "class_name": getattr(info, "class_name", None),
                            "rect": {
                                "left": rect.left,
                                "top": rect.top,
                                "right": rect.right,
                                "bottom": rect.bottom,
                            },
                        }
                    )
                    if len(controls) >= limit:
                        break
                except Exception:
                    continue
            title = window.window_text() or "Foreground window"
            return VisionResult(
                True,
                f"Found {len(controls)} visible UI controls in {title}.",
                {"window_title": title, "hwnd": hwnd, "controls": controls},
            )
        except Exception as exc:
            return VisionResult(False, f"UI inspection failed: {exc}", {"hwnd": hwnd})

    def find_control(self, target: str) -> VisionResult:
        target_norm = " ".join(target.lower().split())
        inspected = self.inspect_controls(limit=160)
        if not inspected.ok:
            return inspected
        controls = inspected.data.get("controls", [])
        exact: list[dict[str, Any]] = []
        partial: list[dict[str, Any]] = []
        for control in controls:
            name = " ".join(str(control.get("name") or "").lower().split())
            if not name:
                continue
            if name == target_norm:
                exact.append(control)
            elif target_norm in name or name in target_norm:
                partial.append(control)
        matches = exact or partial
        if not matches:
            return VisionResult(False, f"Could not find a visible UI control named '{target}'.", {"target": target})
        return VisionResult(True, f"Found UI control '{matches[0].get('name')}'.", {"target": target, "control": matches[0], "matches": matches[:10], "hwnd": inspected.data.get("hwnd")})

    def _windows(self) -> list[dict[str, Any]]:
        if os.name != "nt":
            return []

        user32 = ctypes.windll.user32
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        windows: list[dict[str, Any]] = []

        def callback(hwnd, _lparam):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            title_buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buffer, length + 1)
            title = title_buffer.value.strip()
            if not title:
                return True

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            process_name = None
            try:
                process_name = psutil.Process(int(pid.value)).name()
            except (psutil.Error, OSError):
                pass

            windows.append({
                "title": title,
                "pid": int(pid.value),
                "process": process_name,
                "minimized": bool(user32.IsIconic(hwnd)),
            })
            return True

        try:
            user32.EnumWindows(EnumWindowsProc(callback), 0)
        except OSError:
            return []
        return windows

    def _ocr_text(self, image_path: Path) -> str | None:
        try:
            import pytesseract
            text = pytesseract.image_to_string(str(image_path), config="--psm 6")
        except Exception:
            return None
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)[:5000] or None

    def analyze_desktop(self, image_path: Path | None = None) -> VisionResult:
        snapshot = self.context.snapshot()
        active = snapshot.get("active_window") or {}
        windows = self._windows()
        visible = [item for item in windows if not item.get("minimized")]
        ocr_text = self._ocr_text(image_path) if image_path else None

        lines: list[str] = ["Local desktop analysis complete."]
        if active.get("process") or active.get("title"):
            lines.append(
                f"Active: {active.get('process') or 'Unknown process'}"
                f" — {active.get('title') or 'Untitled window'}"
            )
        if visible:
            lines.append(f"Visible windows: {len(visible)}")
            lines.extend(
                f"• {item['title']} [{item.get('process') or 'unknown'}]"
                for item in visible[:10]
            )
        else:
            lines.append("Visible windows: none detected")
        if ocr_text:
            lines.append("OCR: text detected on screen.")
        else:
            lines.append("OCR: unavailable or no text detected.")

        return VisionResult(
            True,
            "Screen analyzed locally.",
            {
                "active_window": active.get("title"),
                "active_process": active.get("process"),
                "visible_window_count": len(visible),
                "visible_windows": visible[:20],
                "ocr_text": ocr_text,
                "summary": "\n".join(lines),
            },
        )
