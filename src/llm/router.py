"""
LLM 路由与 API Key 管理。
LLMRouter 负责注册 Provider 并按场景路由调用；
APIKeyManager 负责本地持久化保存 Provider 配置。
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .base import LLMConfig
from .providers.auto_recognize import AutoRecognizeProvider

logger = logging.getLogger(__name__)


@dataclass
class APIKeyEntry:
    name: str
    provider: str = ""
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    route_group: str = "default"
    visible_provider: bool = False
    preferred_for: list[str] = field(default_factory=list)
    extra: dict = field(default_factory=dict)


class APIKeyManager:
    """Provider 配置注册表，默认持久化到本地数据目录。"""

    def __init__(self, storage_path: str | Path | None = None):
        self._keys: dict[str, APIKeyEntry] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        self._load()

    def _load(self) -> None:
        if not self.storage_path:
            return
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            payload = json.loads(self.storage_path.read_text(encoding="utf-8"))
            for item in payload:
                entry = APIKeyEntry(**item)
                self._keys[entry.name] = entry
        except Exception as exc:
            logger.warning("APIKeyManager load failed: %s", exc)

    def _save(self) -> None:
        if not self.storage_path:
            return
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {
                "name": item.name,
                "provider": item.provider,
                "base_url": item.base_url,
                "model": item.model,
                "api_key": item.api_key,
                "route_group": item.route_group,
                "visible_provider": item.visible_provider,
                "preferred_for": item.preferred_for,
                "extra": item.extra,
            }
            for item in self._keys.values()
        ]
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_key(self, entry: APIKeyEntry) -> None:
        self._keys[entry.name] = entry
        self._save()
        logger.info("APIKeyManager: registered %s", entry.name)

    def remove_key(self, name: str) -> bool:
        removed = self._keys.pop(name, None) is not None
        if removed:
            self._save()
        return removed

    def get_key(self, name: str) -> Optional[APIKeyEntry]:
        return self._keys.get(name)

    def list_keys(self) -> list[dict]:
        return [
            {
                "name": item.name,
                "provider": item.provider,
                "base_url": item.base_url,
                "model": item.model,
                "route_group": item.route_group,
                "preferred_for": item.preferred_for,
                "visible_provider": item.visible_provider,
                "api_key_masked": _mask_key(item.api_key),
            }
            for item in self._keys.values()
        ]

    def all_entries(self) -> list[APIKeyEntry]:
        return list(self._keys.values())


def _mask_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:3]}***{api_key[-4:]}"


class LLMRouter:
    """
    智能 LLM 路由：
      - register(name, base_url, api_key, model) 注册 Provider
      - route(scenario, messages) 按场景选择 Provider
      - verify_all() 并发验证所有 Provider
    """

    def __init__(self):
        self._providers: dict[str, "AutoRecognizeProvider"] = {}
        self._configs: dict[str, LLMConfig] = {}
        self._metadata: dict[str, dict] = {}
        self._scenario_map: dict[str, str] = {
            "ocr_correction": "default",
            "table_fix": "default",
            "formula_fix": "default",
            "ordering_fix": "default",
            "rag_answer": "default",
        }

    def register(
        self,
        name: str,
        base_url: str,
        api_key: str,
        model: str = "",
        route_group: str = "default",
        preferred_for: list[str] | None = None,
        visible_provider: bool = False,
        extra: dict | None = None,
    ) -> "AutoRecognizeProvider":
        provider = AutoRecognizeProvider.create(base_url, api_key, model)
        self._providers[name] = provider
        self._configs[name] = provider.config
        self._metadata[name] = {
            "route_group": route_group or "default",
            "preferred_for": list(preferred_for or []),
            "visible_provider": bool(visible_provider),
            "extra": extra or {},
        }
        if "default" not in self._providers:
            self._providers["default"] = provider
            self._configs["default"] = provider.config
            self._metadata["default"] = dict(self._metadata[name])
        for scenario in self._metadata[name]["preferred_for"]:
            self._scenario_map[scenario] = name
        logger.info("LLMRouter: registered provider %s (%s)", name, provider.config.provider)
        return provider

    def remove(self, name: str) -> bool:
        removed = self._providers.pop(name, None) is not None
        self._configs.pop(name, None)
        self._metadata.pop(name, None)
        for scenario, bound_name in list(self._scenario_map.items()):
            if bound_name == name:
                self._scenario_map[scenario] = "default"
        if name == "default":
            self._providers.pop("default", None)
            self._configs.pop("default", None)
            self._metadata.pop("default", None)
        return removed

    def hydrate(self, entries: list[APIKeyEntry]) -> None:
        for entry in entries:
            try:
                self.register(
                    entry.name,
                    entry.base_url,
                    entry.api_key,
                    entry.model,
                    route_group=entry.route_group,
                    preferred_for=entry.preferred_for,
                    visible_provider=entry.visible_provider,
                    extra=entry.extra,
                )
            except Exception as exc:
                logger.warning("Failed to hydrate provider %s: %s", entry.name, exc)

    def list_providers(self) -> list[dict]:
        rows = []
        for name, config in self._configs.items():
            if name == "default":
                continue
            meta = self._metadata.get(name, {})
            rows.append(
                {
                    "name": name,
                    "provider": config.provider if meta.get("visible_provider") else "",
                    "model": config.model,
                    "base_url": config.base_url,
                    "route_group": meta.get("route_group", "default"),
                    "preferred_for": meta.get("preferred_for", []),
                    "extra": meta.get("extra", {}),
                }
            )
        return rows

    def get(self, name: str) -> Optional["AutoRecognizeProvider"]:
        return self._providers.get(name)

    def _route_rank(self, name: str) -> tuple[int, str]:
        meta = self._metadata.get(name, {})
        group = meta.get("route_group", "default")
        priority = {"primary": 0, "default": 1, "secondary": 2}.get(group, 3)
        return priority, name

    def _candidate_names(self, scenario: str) -> list[str]:
        preferred = self._scenario_map.get(scenario, "default")
        names = [preferred] if preferred in self._providers else []
        others = [name for name in self._providers.keys() if name not in {"default", preferred}]
        others.sort(key=self._route_rank)
        if "default" in self._providers and "default" not in names:
            names.append("default")
        names.extend(others)
        deduped = []
        seen = set()
        for name in names:
            if name in seen:
                continue
            seen.add(name)
            deduped.append(name)
        return deduped

    async def route(self, scenario: str, messages: list[dict], **kwargs) -> str:
        candidates = self._candidate_names(scenario)
        if not candidates:
            raise RuntimeError(f"No LLM provider available for scenario '{scenario}'")
        last_error = None
        for name in candidates:
            provider = self._providers.get(name)
            if provider is None:
                continue
            try:
                response = await provider.chat(messages, **kwargs)
                if response.success:
                    return response.content
                last_error = response.error or f"{name} returned unsuccessful response"
            except Exception as exc:
                last_error = f"{name}: {exc}"
                logger.warning("LLM route fallback: %s failed for %s: %s", name, scenario, exc)
        raise RuntimeError(last_error or f"No LLM provider available for scenario '{scenario}'")

    async def verify_all(self) -> dict:
        results: dict[str, bool] = {}
        tasks = []
        names = [name for name in self._providers.keys() if name != "default"]
        for name in names:
            tasks.append((name, self._providers[name].verify_connection()))
        coroutines = [item[1] for item in tasks]
        if coroutines:
            outcomes = await asyncio.gather(*coroutines, return_exceptions=True)
            for (name, _), outcome in zip(tasks, outcomes):
                results[name] = False if isinstance(outcome, Exception) else bool(outcome)
        return results
