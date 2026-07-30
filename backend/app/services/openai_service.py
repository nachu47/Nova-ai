import hashlib
import math
from typing import Any

import httpx

from app.core.config import settings

OPENAI_BASE = "https://api.openai.com/v1"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}


def deterministic_embedding(text: str, dimensions: int = 256) -> list[float]:
    vector = [0.0] * dimensions
    words = text.lower().split()
    for word in words:
        digest = hashlib.sha256(word.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def create_embedding(text: str) -> list[float]:
    if not settings.openai_api_key:
        return deterministic_embedding(text)
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{OPENAI_BASE}/embeddings",
            headers=_headers(),
            json={"model": settings.openai_embedding_model, "input": text},
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


def chat_json(system: str, user: str, schema_name: str, schema: dict[str, Any]) -> dict[str, Any]:
    if not settings.openai_api_key:
        return {
            "summary": user[:500] if user else "No transcript was available.",
            "key_points": [],
            "action_items": [],
            "disposition": "completed",
            "sentiment": "neutral",
            "structured_data": {},
        }
    payload = {
        "model": settings.openai_text_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
        "temperature": 0.2,
    }
    with httpx.Client(timeout=60) as client:
        response = client.post(f"{OPENAI_BASE}/chat/completions", headers=_headers(), json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
    import json
    return json.loads(content)
