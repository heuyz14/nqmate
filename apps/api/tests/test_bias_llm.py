import unittest
import httpx

from nqmate_api.bias.models import BiasResult
from nqmate_api.bias.llm import GeminiBiasExplainer


def result() -> BiasResult:
    return BiasResult("BULLISH", 0.42, 0.42, "MONITOR", None, ("gap",), ("gap",), ("macro_context",), ("score crosses neutral",), ("heuristic score",))


class BiasLlmTests(unittest.TestCase):
    def test_gemini_explainer_returns_strict_structured_output(self) -> None:
        def handler(request):
            payload = '{"direction":"BULLISH","confidence":0.4,"summary":"Positive structure","bull_case":["gap"],"bear_case":["macro_context"],"invalidation":["score crosses neutral"],"risks":["heuristic score"]}'
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": payload}]}}]}, request=request)

        explainer = GeminiBiasExplainer("test-key", client=httpx.Client(transport=httpx.MockTransport(handler)))
        explanation = explainer.explain(result())
        self.assertEqual(explanation.direction, "BULLISH")
        self.assertEqual(explanation.summary, "Positive structure")

    def test_gemini_explainer_rejects_invalid_confidence(self) -> None:
        def handler(request):
            payload = '{"direction":"BULLISH","confidence":2,"summary":"bad"}'
            return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": payload}]}}]}, request=request)

        explainer = GeminiBiasExplainer("test-key", client=httpx.Client(transport=httpx.MockTransport(handler)))
        with self.assertRaises(ValueError):
            explainer.explain(result())
