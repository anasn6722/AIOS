from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from PIL import ImageGrab
except ImportError:  # pragma: no cover - optional dependency in non-GUI test envs
    ImageGrab = None  # type: ignore[assignment]

from ai.context import ContextEngine


@dataclass(frozen=True)
class VisionResult:
    ok: bool
    message: str
    data: dict[str, Any]


class VisionEngine:
    """Local screen-capture foundation for the AIOS vision layer.

    This milestone is deliberately non-invasive: it captures the current screen
    and combines it with read-only OS context. Future vision models can consume
    the saved image without receiving direct OS execution privileges.
    """

    def __init__(self, context: ContextEngine) -> None:
        self.context = context
        self.capture_dir = Path.home() / ".aios" / "captures"

    def capture_screen(self) -> VisionResult:
        if ImageGrab is None:
            return VisionResult(
                False,
                "Vision capture unavailable. Install Pillow in the AIOS environment.",
                {},
            )
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.capture_dir / f"screen_{stamp}.png"
        try:
            image = ImageGrab.grab(all_screens=True)
            image.save(target)
        except (OSError, ValueError) as exc:
            return VisionResult(False, f"Screen capture failed: {exc}", {})

        active = self.context.snapshot().get("active_window", {})
        return VisionResult(
            True,
            "Screen captured for AIOS vision processing.",
            {
                "image": str(target),
                "width": image.width,
                "height": image.height,
                "active_process": active.get("process"),
                "active_window": active.get("title"),
            },
        )
