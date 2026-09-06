from __future__ import annotations

"""Lean Ollama HTTP client with bounded generation and useful diagnostics."""

import json
import time
from typing import Any, Callable

import requests

DEFAULT_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:7b"


class OllamaError(RuntimeError):
    pass


def is_available(base_url: str = DEFAULT_BASE_URL, timeout: float = 2.0) -> bool:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        return response.ok
    except requests.RequestException:
        return False


def list_models(base_url: str = DEFAULT_BASE_URL, timeout: float = 3.0) -> list[str]:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        response.raise_for_status()
        return [m.get("name", "") for m in response.json().get("models", []) if m.get("name")]
    except requests.RequestException:
        return []


def generate_json(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    schema: dict[str, Any] | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 210,
    num_ctx: int = 8192,
    num_predict: int = 2600,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    if not is_available(base_url):
        raise OllamaError("Ollama n'est pas disponible sur http://127.0.0.1:11434")

    if progress_callback:
        progress_callback(f"Envoi au modèle {model}…")

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "keep_alive": "20m",
        "options": {
            "temperature": 0,
            "num_ctx": num_ctx,
            "num_predict": num_predict,
            "repeat_penalty": 1.05,
        },
        "format": schema if schema is not None else "json",
    }

    started = time.monotonic()
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/generate",
            json=payload,
            timeout=(10, timeout),
        )
        response.raise_for_status()
    except requests.Timeout as exc:
        raise OllamaError(
            f"Le modèle a dépassé {timeout} secondes. Réessayez avec moins de pages ou le modèle qwen2.5:3b."
        ) from exc
    except requests.RequestException as exc:
        raise OllamaError(f"Erreur de communication avec Ollama : {exc}") from exc

    elapsed = time.monotonic() - started
    body = response.json()
    raw = body.get("response", "")
    if progress_callback:
        progress_callback(f"Réponse reçue en {elapsed:.0f} s · validation en cours…")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        preview = raw[:500].replace("\n", " ")
        raise OllamaError(f"Le modèle n'a pas renvoyé un JSON valide : {preview}") from exc
