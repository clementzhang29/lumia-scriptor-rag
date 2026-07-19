import unittest

from src.llm.base import LLMConfig, LLMResponse
from src.llm.router import LLMRouter


class _DummyProvider:
    def __init__(self, name: str, should_fail: bool):
        self.config = LLMConfig(provider=name, model=f"{name}-model", base_url="https://example.com")
        self.should_fail = should_fail

    async def chat(self, messages, **kwargs):
        if self.should_fail:
            raise RuntimeError(f"{self.config.provider} failed")
        return LLMResponse(content="OK", model=self.config.model, provider=self.config.provider)

    async def verify_connection(self):
        return not self.should_fail


class LLMRouterFallbackTest(unittest.IsolatedAsyncioTestCase):
    async def test_route_falls_back_when_primary_fails(self):
        router = LLMRouter()
        router._providers = {
            "gpt-main": _DummyProvider("gpt-main", should_fail=True),
            "omni-catalog": _DummyProvider("omni-catalog", should_fail=False),
            "default": _DummyProvider("default", should_fail=False),
        }
        router._metadata = {
            "gpt-main": {"route_group": "primary", "preferred_for": ["ocr_correction"], "visible_provider": False, "extra": {}},
            "omni-catalog": {"route_group": "secondary", "preferred_for": [], "visible_provider": False, "extra": {}},
            "default": {"route_group": "default", "preferred_for": [], "visible_provider": False, "extra": {}},
        }
        router._scenario_map["ocr_correction"] = "gpt-main"

        result = await router.route("ocr_correction", [{"role": "user", "content": "hello"}])
        self.assertEqual(result, "OK")


if __name__ == "__main__":
    unittest.main()
