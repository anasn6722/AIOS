from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ActionRequest:
    name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    risk: RiskLevel = RiskLevel.SAFE
    source: str = "manual"


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    message: str
    data: dict[str, Any] = field(default_factory=dict)
