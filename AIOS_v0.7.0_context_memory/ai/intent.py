from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.actions import RiskLevel


@dataclass(frozen=True)
class OSIntent:
    action: str
    target_type: str | None = None
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    risk: RiskLevel = RiskLevel.SAFE
    confidence: float = 1.0
    explanation: str = ""
