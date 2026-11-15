"""Minimal client for any OpenAI-compatible chat-completions API.

Works with OpenAI, Google Gemini's OpenAI-compatible endpoint, Groq, a local
Ollama server and others. Configured through environment variables:

    ASSETFLOW_LLM_BASE_URL   e.g. https://api.openai.com/v1
    ASSETFLOW_LLM_MODEL      the model name your provider expects
    ASSETFLOW_LLM_API_KEY    optional for local servers such as Ollama

Uses only the standard library, so the app gains no new dependency.
"""

import json
import os
import urllib.error
import urllib.request

TIMEOUT_SECONDS = 20


class LLMError(Exception):
    """The language model could not be reached or returned something unusable."""


def _settings() -> dict:
    # Read at call time so configuration can change without re-importing.
    return {
        "base_url": os.getenv("ASSETFLOW_LLM_BASE_URL", "").strip().rstrip("/"),
        "model": os.getenv("ASSETFLOW_LLM_MODEL", "").strip(),
        "api_key": os.getenv("ASSETFLOW_LLM_API_KEY", "").strip(),
    }


def is_configured() -> bool:
    s = _settings()
    return bool(s["model"]) and s["base_url"].startswith(("http://", "https://"))


def complete(system: str, user: str) -> str:
    """Send one system + user message and return the model's text reply."""
    if not is_configured():
        raise LLMError("AI search is not configured")
    s = _settings()

    payload = {
        "model": s["model"],
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    headers = {"Content-Type": "application/json"}
    if s["api_key"]:
        headers["Authorization"] = f"Bearer {s['api_key']}"

    request = urllib.request.Request(
        f"{s['base_url']}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        raise LLMError(f"The AI provider answered with HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise LLMError("The AI provider could not be reached") from exc
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError("The AI provider returned an unexpected response") from exc

    if not isinstance(content, str) or not content.strip():
        raise LLMError("The AI provider returned an empty answer")
    return content
