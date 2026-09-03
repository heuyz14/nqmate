from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from nqmate_api.bias.models import BiasResult


@dataclass(frozen=True)
class BiasExplanation:
    direction: str
    confidence: float
    summary: str
    bull_case: tuple[str, ...]
    bear_case: tuple[str, ...]
    invalidation: tuple[str, ...]
    risks: tuple[str, ...]


class LLMProvider(Protocol):
    def explain_bias(self, result: BiasResult) -> BiasExplanation: ...


class GeminiBiasExplainer:
    def __init__(self, api_key: str, model: str = "gemini-3.6-flash", client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(timeout=30)
        self._url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        self._api_key = api_key

    def explain(self, result: BiasResult) -> BiasExplanation:
        evidence = {
            "direction": result.direction, "score": result.score, "confidence": result.confidence,
            "recommendation": result.recommendation, "catalyst_risk": result.catalyst_risk,
            "evidence": result.evidence, "bull_case": result.bull_case,
            "bear_case": result.bear_case, "invalidation": result.invalidation,
            "uncertainty": result.uncertainty,
        }
        prompt = "Explain this supplied deterministic NQ bias. Do not calculate, add, or contradict facts. Return JSON only with direction, confidence, summary, bull_case, bear_case, invalidation, and risks. Evidence: " + json.dumps(evidence)
        response = self._client.post(self._url, params={"key": self._api_key}, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}})
        response.raise_for_status()
        payload: Any = response.json()
        values = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
        if not isinstance(values, dict) or not isinstance(values.get("summary"), str):
            raise ValueError("bias explanation must contain a summary")
        confidence = values.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError("bias explanation confidence must be between 0 and 1")
        return BiasExplanation(
            direction=str(values.get("direction", result.direction)), confidence=float(confidence),
            summary=values["summary"], bull_case=tuple(values.get("bull_case") or ()),
            bear_case=tuple(values.get("bear_case") or ()), invalidation=tuple(values.get("invalidation") or ()),
            risks=tuple(values.get("risks") or ()),
        )
