"""Explainability Layer (FR-600 series). ADR-009: Gemini free tier primary, Groq
fallback. The LLM only ever receives already-computed numbers and is instructed to
translate them into prose — it never performs arithmetic or makes the underlying
decision. If no API key is configured, falls back to a deterministic template so
the rest of the product still works end-to-end without a key (important for local
dev / grading without secrets).
"""
import json

import httpx

from app.config import settings

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_INSTRUCTION = (
    "You are OrgBrain's explanation layer. You are given pre-computed, deterministic "
    "results (never raw opinions). Explain them in plain, direct language for a "
    "non-technical stakeholder. Always include: the evidence, the reasoning, key "
    "assumptions, and at least one alternative. Never invent numbers not present in "
    "the input. Keep it under 150 words."
)


def _template_fallback(context: dict) -> str:
    """Deterministic, no-API-key-required explanation so the product works offline."""
    parts = [f"{k.replace('_', ' ')}: {v}" for k, v in context.items() if v is not None]
    return (
        "Explanation (offline template — configure GEMINI_API_KEY for natural-language output): "
        + "; ".join(parts)
    )


def _call_gemini(context: dict) -> str | None:
    if not settings.gemini_api_key:
        return None
    try:
        resp = httpx.post(
            f"{GEMINI_URL}?key={settings.gemini_api_key}",
            json={
                "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                "contents": [{"parts": [{"text": json.dumps(context)}]}],
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def _call_groq(context: dict) -> str | None:
    if not settings.groq_api_key:
        return None
    try:
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": json.dumps(context)},
                ],
            },
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


def explain(context: dict) -> str:
    """FR-601: Provide Explainable Recommendations. Tries Gemini, then Groq, then
    falls back to a deterministic template — always returns something."""
    return _call_gemini(context) or _call_groq(context) or _template_fallback(context)


def answer_follow_up(context: dict, question: str) -> str:
    """FR-602: Answer Follow-Up Questions. Same fallback chain, scoped to the
    original context so answers stay grounded in real numbers instead of hallucinating."""
    payload = {"original_context": context, "follow_up_question": question}
    result = _call_gemini(payload) or _call_groq(payload)
    if result:
        return result
    return (
        f"(offline template) Based on the recorded evidence {json.dumps(context)}, "
        f"I can't generate a free-text answer to '{question}' without an LLM key configured — "
        f"but the underlying numbers above are accurate and computed deterministically."
    )
