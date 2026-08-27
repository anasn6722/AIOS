from __future__ import annotations

import json
import re
from typing import Any

from ai.intent import OSIntent
from ai.llm_client import LocalLLMClient
from core.actions import RiskLevel


ALLOWED_ACTIONS = {
    "system_info", "open_path", "launch_app", "show_desktop", "lock_computer",
    "shutdown", "restart", "list_apps", "search_files", "search_files_modified",
    "list_processes", "close_process",
}
ALLOWED_OBJECT_TYPES = {None, "application", "file", "folder", "workspace", "process", "task", "setting", "file_or_folder"}


class LLMPlanner:
    """Converts natural language to a strictly validated OSIntent JSON object."""

    def __init__(self, client: LocalLLMClient | None = None) -> None:
        self.client = client or LocalLLMClient()

    def plan(self, text: str) -> OSIntent | None:
        response = self.client.generate(self._prompt(text))
        if not response:
            return None
        payload = self._parse_json(response)
        if payload is None:
            return None
        return self._validate(payload, text)

    @staticmethod
    def _prompt(text: str) -> str:
        schema = {
            "action": "one allowed action",
            "target_type": "application|file|folder|workspace|process|setting|file_or_folder|null",
            "target": "string or null",
            "parameters": "object",
            "risk": "safe|low|medium|high|critical",
            "confidence": "number 0..1",
            "explanation": "short reason",
        }
        return (
            "You are the planning layer of AIOS, a Windows AI operating environment. "
            "You DO NOT execute commands. Return ONLY one JSON object, no markdown. "
            "Never invent shell commands or Python code. Choose only from these actions: "
            "system_info, open_path, launch_app, show_desktop, lock_computer, shutdown, "
            "restart, list_apps, search_files, search_files_modified, list_processes, close_process. "
            "For file searches put the query in parameters.query. For app launches put the app name in parameters.app. "
            "For paths put the filesystem path in parameters.path. "
            f"JSON schema: {json.dumps(schema)}\nUser request: {text}"
        )

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any] | None:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S).strip()
        try:
            value = json.loads(cleaned)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, flags=re.S)
            if not match:
                return None
            try:
                value = json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return value if isinstance(value, dict) else None

    @staticmethod
    def _validate(data: dict[str, Any], original: str) -> OSIntent | None:
        action = str(data.get("action", "")).strip()
        target_type = data.get("target_type")
        if action not in ALLOWED_ACTIONS or target_type not in ALLOWED_OBJECT_TYPES:
            return None
        target = data.get("target")
        target = str(target) if target is not None else None
        parameters = data.get("parameters")
        if not isinstance(parameters, dict):
            parameters = {}
        risk_raw = str(data.get("risk", "safe")).lower()
        try:
            risk = RiskLevel(risk_raw)
        except ValueError:
            return None
        try:
            confidence = min(1.0, max(0.0, float(data.get("confidence", 0.5))))
        except (TypeError, ValueError):
            confidence = 0.5
        explanation = str(data.get("explanation", "Local model interpretation.")).strip()
        # Safety normalization: action-specific requirements are enforced locally.
        if action == "launch_app" and not parameters.get("app") and target:
            parameters["app"] = target
        if action == "search_files" and not parameters.get("query") and target:
            parameters["query"] = target
        if action == "open_path" and not parameters.get("path") and target:
            parameters["path"] = target
        return OSIntent(action, target_type, target, parameters, risk, confidence, explanation or "Local model interpretation.")
