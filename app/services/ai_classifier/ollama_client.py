from __future__ import annotations

import json

import requests

from app.config import get_settings


class OllamaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    def generate_json(self, prompt: str, schema: dict | None = None) -> dict:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": schema or "json",
            "stream": False,
            "options": {"temperature": 0},
        }

        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload,
            timeout=self.timeout,
        )

        if response.status_code >= 400 and schema is not None:
            fallback_payload = dict(payload)
            fallback_payload["format"] = "json"
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=fallback_payload,
                timeout=self.timeout,
            )

        response.raise_for_status()

        body = response.json()
        raw = body.get("response", "")
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("Ollama response missing JSON string in `response` field")

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Ollama returned non-JSON content") from exc

        if not isinstance(parsed, dict):
            raise ValueError("Ollama JSON payload must be an object")

        return parsed
