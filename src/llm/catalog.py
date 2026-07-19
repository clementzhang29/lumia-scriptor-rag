import asyncio
import json
from typing import Any

import httpx


def _normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def _api_root(base_url: str) -> str:
    normalized = _normalize_base_url(base_url)
    return normalized[:-3] if normalized.endswith("/v1") else normalized


async def fetch_openai_models(base_url: str, api_key: str) -> list[dict]:
    url = _api_root(base_url) + "/v1/models"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("data", []) if isinstance(data, dict) else []


async def fetch_vveai_pricing(base_url: str, api_key: str) -> dict[str, dict]:
    url = _api_root(base_url) + "/api/pricing"
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
    pricing = {}
    for item in data.get("data", []) if isinstance(data, dict) else []:
        key = item.get("key") or item.get("model_name")
        if not key:
            continue
        pricing[key] = {
            "price_type": item.get("quota_type"),
            "input_ratio": item.get("model_ratio"),
            "output_ratio": item.get("completion_ratio"),
            "fixed_price": item.get("model_price"),
            "description": item.get("description", ""),
            "endpoints": item.get("endpoints", []),
            "tags": [tag.get("name") for tag in item.get("tags", []) if tag.get("name")],
        }
    return pricing


async def fetch_catalog(base_url: str, api_key: str) -> dict[str, Any]:
    normalized = _normalize_base_url(base_url)
    try:
        models = await fetch_openai_models(normalized, api_key)
    except Exception as exc:
        return {"models": [], "error": str(exc), "pricing": {}}

    pricing = {}
    if "api.vveai.com" in normalized:
        try:
            pricing = await fetch_vveai_pricing(normalized, api_key)
        except Exception:
            pricing = {}

    rows = []
    for model in models:
        model_id = model.get("id", "")
        meta = pricing.get(model_id, {})
        rows.append(
            {
                "id": model_id,
                "label": model_id,
                "group": "default",
                "price_type": meta.get("price_type"),
                "input_ratio": meta.get("input_ratio"),
                "output_ratio": meta.get("output_ratio"),
                "fixed_price": meta.get("fixed_price"),
                "description": meta.get("description", ""),
                "endpoints": meta.get("endpoints", []),
                "tags": meta.get("tags", []),
            }
        )
    rows.sort(key=lambda item: item["id"].lower())
    return {"models": rows, "pricing": pricing, "error": ""}
