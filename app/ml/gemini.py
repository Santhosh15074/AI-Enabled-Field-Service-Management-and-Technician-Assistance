"""The one place the app talks to Google Gemini. Every AI feature built on it (the troubleshooting
fallback, triage, report structuring, assignment suggestions) goes through generate(), which never
raises: no key, a timeout, a refusal or a network fault all come back as None, and each caller
then falls back to what it did before AI existed. A review demo with bad Wi-Fi still works.

Speed: a "lite" model with thinking at its minimum and one reused HTTPS connection usually answers
in about 1 s. But any one model has slow spells (gemini-3.1-flash-lite went from 1.3 s to 4-12 s in
the same afternoon), so calls are hedged: if the main model hasn't answered within
ai_hedge_after_seconds, the same request also goes to a backup model, and whichever answers first
wins. Structured answers use Gemini's JSON-schema mode, so a caller gets a dict
of the fields it asked for rather than free text it has to parse.
"""

import json
import logging
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from functools import lru_cache
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


@lru_cache(maxsize=1)
def _client() -> httpx.Client:
    # Reused, so after the first call each one skips the TLS handshake with Google.
    return httpx.Client()


def enabled() -> bool:
    return bool(get_settings().gemini_api_key)


def model_name() -> str:
    """Saved alongside whatever the model produced. The main model: a hedged call may occasionally
    have been answered by the backup instead."""
    return f"google:{get_settings().ai_fallback_model}"


# Shared by every hedged call; two slots per call at most, and calls are short.
_pool = ThreadPoolExecutor(max_workers=8, thread_name_prefix="gemini")


def generate(
    instructions: str, prompt: str, *, schema: dict | None = None, max_tokens: int = 400
) -> str | dict[str, Any] | None:
    """Plain text, or with `schema` (a JSON Schema object) a dict matching it. None on any failure."""
    settings = get_settings()
    if not settings.gemini_api_key or not prompt.strip():
        return None
    config: dict[str, Any] = {
        "maxOutputTokens": max_tokens,
        "temperature": 0.2,
        "thinkingConfig": {"thinkingLevel": "minimal"},
    }
    if schema is not None:
        config |= {"responseMimeType": "application/json", "responseJsonSchema": schema}
    body = {
        "systemInstruction": {"parts": [{"text": instructions}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": config,
    }

    models = [settings.ai_fallback_model]
    if settings.ai_backup_model and settings.ai_backup_model != settings.ai_fallback_model:
        models.append(settings.ai_backup_model)
    pending = {_pool.submit(_call, models[0], body, schema is not None)}
    started_backup = len(models) == 1
    deadline = settings.ai_fallback_timeout_seconds
    waited = 0.0
    while pending:
        window = deadline - waited if started_backup else min(settings.ai_hedge_after_seconds, deadline)
        done, pending = wait(pending, timeout=window, return_when=FIRST_COMPLETED)
        waited += window if not done else 0
        for future in done:
            if (answer := future.result()) is not None:
                return answer
        if not started_backup:
            # Slow or failed: the backup races whatever the main model is still doing.
            pending.add(_pool.submit(_call, models[1], body, schema is not None))
            started_backup = True
        elif not done:
            break  # past the deadline
    return None


def _call(model: str, body: dict, structured: bool) -> str | dict[str, Any] | None:
    settings = get_settings()
    try:
        response = _client().post(
            _API.format(model=model),
            json=body,
            headers={"x-goog-api-key": settings.gemini_api_key},
            timeout=settings.ai_fallback_timeout_seconds,
        )
        response.raise_for_status()
        candidate = response.json()["candidates"][0]
        text = "".join(part.get("text", "") for part in candidate["content"]["parts"]).strip()
        if not structured:
            return text or None
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except httpx.HTTPStatusError as error:
        # The body says why (bad key, quota, unknown model); it never contains the key itself.
        logger.warning("Gemini %s failed: HTTP %s %s", model, error.response.status_code, error.response.text[:300])
        return None
    except Exception as error:
        logger.warning("Gemini %s failed: %r", model, error)
        return None
