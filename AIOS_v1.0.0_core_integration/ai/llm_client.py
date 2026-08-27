from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib import error, request


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool = False
    provider: str = "ollama"
    base_url: str = "http://127.0.0.1:11434"
    model: str = "qwen3:4b"
    timeout_seconds: float = 12.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        enabled = os.getenv("AIOS_LLM_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
        return cls(
            enabled=enabled,
            provider=os.getenv("AIOS_LLM_PROVIDER", "ollama").strip().lower(),
            base_url=os.getenv("AIOS_LLM_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
            model=os.getenv("AIOS_LLM_MODEL", "qwen3:4b").strip(),
            timeout_seconds=float(os.getenv("AIOS_LLM_TIMEOUT", "12")),
        )


class LocalLLMClient:
    """Optional localhost LLM client. It only returns text; it never executes OS actions."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig.from_env()

    def available(self) -> bool:
        if not self.config.enabled or self.config.provider != "ollama":
            return False
        try:
            with request.urlopen(f"{self.config.base_url}/api/tags", timeout=2.5) as response:
                return response.status == 200
        except (OSError, error.URLError):
            return False

    def generate(self, prompt: str) -> str | None:
        if not self.config.enabled or self.config.provider != "ollama":
            return None
        payload = json.dumps(
            {
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0},
            }
        ).encode("utf-8")
        req = request.Request(
            f"{self.config.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (OSError, error.URLError, TimeoutError, json.JSONDecodeError):
            return None
        text = data.get("response")
        return text.strip() if isinstance(text, str) and text.strip() else None
