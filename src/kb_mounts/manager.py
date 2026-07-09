import json
import re
import shutil
import uuid
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, UTC
from pathlib import Path


SUPPORTED_EXTS = {".epub", ".pdf", ".txt", ".md", ".html", ".htm", ".docx"}
SECRET_FIELD_HINTS = ("password", "token", "secret", "api_key", "access_key")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_rel_path(path: str) -> str:
    rel = path.replace("\\", "/").strip("/")
    if not rel:
        return ""
    return "/".join(part for part in rel.split("/") if part not in {"", ".", ".."})


def _ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def _safe_cache_name(name: str) -> str:
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", str(name or "")).strip()
    text = re.sub(r"\s+", "_", text)
    return text[:60] or "source"


class BaseMountProvider:
    def __init__(self, source: dict):
        self.source = source
        self.config = source.get("config", {})

    def list_files(self) -> list[dict]:
        raise NotImplementedError

    def download(self, file_info: dict, dest_path: Path):
        raise NotImplementedError


class LocalDirectoryProvider(BaseMountProvider):
    def list_files(self) -> list[dict]:
        root = Path(self.config["root_path"]).expanduser()
        files = []
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTS:
                continue
            rel_path = path.relative_to(root).as_posix()
            stat = path.stat()
            files.append(
                {
                    "rel_path": rel_path,
                    "size": stat.st_size,
                    "modified_at": int(stat.st_mtime),
                    "source_path": str(path),
                }
            )
        return files

    def download(self, file_info: dict, dest_path: Path):
        _ensure_parent(dest_path)
        shutil.copy2(file_info["source_path"], dest_path)


class WebDAVProvider(BaseMountProvider):
    NS = {"d": "DAV:"}

    def __init__(self, source: dict):
        super().__init__(source)
        self.base_url = self.config["base_url"].rstrip("/")
        self.root_path = self.config.get("root_path", "/").strip() or "/"
        if not self.root_path.startswith("/"):
            self.root_path = "/" + self.root_path
        self.username = self.config.get("username", "")
        self.password = self.config.get("password", "")

    def _build_request(self, url: str, method: str = "GET", body: bytes | None = None, content_type: str | None = None):
        request = urllib.request.Request(url, data=body, method=method)
        if content_type:
            request.add_header("Content-Type", content_type)
        if self.username or self.password:
            password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            password_mgr.add_password(None, self.base_url, self.username, self.password)
            opener = urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(password_mgr))
            return opener, request
        return urllib.request, request

    def _request_text(self, url: str, method: str = "GET", body: bytes | None = None, content_type: str | None = None) -> str:
        opener, request = self._build_request(url, method, body, content_type)
        with opener.open(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _request_bytes(self, url: str) -> bytes:
        opener, request = self._build_request(url, "GET")
        with opener.open(request, timeout=60) as response:
            return response.read()

    def _list_dir(self, current_path: str) -> list[dict]:
        encoded_path = "/".join(urllib.parse.quote(part) for part in current_path.strip("/").split("/") if part)
        url = f"{self.base_url}/{encoded_path}" if encoded_path else self.base_url + "/"
        xml = self._request_text(
            url,
            method="PROPFIND",
            body=b"""<?xml version="1.0" encoding="utf-8" ?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/><d:getcontentlength/><d:getlastmodified/></d:prop></d:propfind>""",
            content_type="application/xml",
        )
        root = ET.fromstring(xml)
        items = []
        for response in root.findall("d:response", self.NS):
            href = response.findtext("d:href", default="", namespaces=self.NS)
            if not href:
                continue
            decoded_href = urllib.parse.unquote(href)
            if decoded_href.rstrip("/").endswith(current_path.rstrip("/")):
                continue
            prop = response.find("d:propstat/d:prop", self.NS)
            if prop is None:
                continue
            is_dir = prop.find("d:resourcetype/d:collection", self.NS) is not None
            rel = decoded_href.replace(self.root_path, "", 1).strip("/")
            items.append(
                {
                    "rel_path": rel,
                    "is_dir": is_dir,
                    "size": int(prop.findtext("d:getcontentlength", default="0", namespaces=self.NS) or 0),
                    "modified_at": prop.findtext("d:getlastmodified", default="", namespaces=self.NS),
                }
            )
        return items

    def list_files(self) -> list[dict]:
        files = []
        queue = [self.root_path]
        while queue:
            current = queue.pop(0)
            for item in self._list_dir(current):
                rel_path = _safe_rel_path(item["rel_path"])
                if not rel_path:
                    continue
                remote_path = f"{self.root_path.rstrip('/')}/{rel_path}".replace("//", "/")
                if item["is_dir"]:
                    queue.append(remote_path)
                elif Path(rel_path).suffix.lower() in SUPPORTED_EXTS:
                    files.append(
                        {
                            "rel_path": rel_path,
                            "size": item["size"],
                            "modified_at": item["modified_at"],
                            "remote_path": remote_path,
                        }
                    )
        return files

    def download(self, file_info: dict, dest_path: Path):
        remote_path = "/".join(urllib.parse.quote(part) for part in file_info["remote_path"].strip("/").split("/") if part)
        url = f"{self.base_url}/{remote_path}"
        content = self._request_bytes(url)
        _ensure_parent(dest_path)
        dest_path.write_bytes(content)


class AlistProvider(BaseMountProvider):
    def __init__(self, source: dict):
        super().__init__(source)
        self.base_url = self.config["base_url"].rstrip("/")
        self.root_path = self.config.get("root_path", "/").strip() or "/"
        if not self.root_path.startswith("/"):
            self.root_path = "/" + self.root_path
        self.token = self.config.get("token", "")
        self.password = self.config.get("password", "")

    def _request_json(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": self.token},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", errors="ignore"))

    def _list_dir(self, current_path: str) -> list[dict]:
        response = self._request_json(
            "/api/fs/list",
            {
                "path": current_path,
                "password": self.password,
                "page": 1,
                "per_page": 0,
                "refresh": False,
            },
        )
        return response.get("data", {}).get("content", []) if response.get("code") == 200 else []

    def list_files(self) -> list[dict]:
        files = []
        queue = [self.root_path]
        while queue:
            current = queue.pop(0)
            for item in self._list_dir(current):
                name = item.get("name", "").strip()
                if not name:
                    continue
                full_path = f"{current.rstrip('/')}/{name}".replace("//", "/")
                rel_path = _safe_rel_path(full_path.replace(self.root_path, "", 1))
                if item.get("is_dir"):
                    queue.append(full_path)
                elif Path(name).suffix.lower() in SUPPORTED_EXTS:
                    files.append(
                        {
                            "rel_path": rel_path,
                            "size": int(item.get("size") or 0),
                            "modified_at": item.get("modified", ""),
                            "remote_path": full_path,
                        }
                    )
        return files

    def download(self, file_info: dict, dest_path: Path):
        quoted = urllib.parse.quote(file_info["remote_path"].lstrip("/"), safe="/")
        request = urllib.request.Request(
            f"{self.base_url}/d/{quoted}",
            headers={"Authorization": self.token},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            content = response.read()
        _ensure_parent(dest_path)
        dest_path.write_bytes(content)


class KnowledgeMountManager:
    PROVIDERS = {
        "local_dir": LocalDirectoryProvider,
        "webdav": WebDAVProvider,
        "alist": AlistProvider,
    }

    def __init__(self, data_root: str | Path):
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.mounts_root = self.data_root / "mounts"
        self.mounts_root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.data_root / "kb_sources.json"
        if not self.registry_path.exists():
            self.registry_path.write_text("[]", encoding="utf-8")

    def _load_registry(self) -> list[dict]:
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_registry(self, sources: list[dict]):
        self.registry_path.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cache_dir_for(self, source_id: str, name: str) -> str:
        return str(self.mounts_root / f"{source_id}_{_safe_cache_name(name)}")

    def _validate_source_payload(self, data: dict):
        name = str(data.get("name", "")).strip()
        if not name:
            raise ValueError("Knowledge source name is required")
        source_type = str(data.get("type", "")).strip()
        if source_type not in self.PROVIDERS:
            raise ValueError(f"Unsupported source type: {source_type}")

    def _merge_config(self, current_config: dict, incoming_config: dict | None, source_type_changed: bool = False) -> dict:
        if incoming_config is None:
            return dict(current_config or {})
        if source_type_changed:
            return {key: value for key, value in incoming_config.items() if value not in (None, "")}
        merged = dict(current_config or {})
        for key, value in incoming_config.items():
            if value in (None, ""):
                if any(hint in key.lower() for hint in SECRET_FIELD_HINTS) and key in merged:
                    continue
                if key in merged and not any(hint in key.lower() for hint in SECRET_FIELD_HINTS):
                    merged.pop(key, None)
                continue
            merged[key] = value
        return merged

    def list_sources(self) -> list[dict]:
        return self._load_registry()

    def get_source(self, source_id: str) -> dict:
        for source in self._load_registry():
            if source["id"] == source_id:
                return source
        raise KeyError(source_id)

    def add_source(self, data: dict) -> dict:
        self._validate_source_payload(data)
        sources = self._load_registry()
        source_id = uuid.uuid4().hex[:12]
        source_name = data["name"].strip()
        source = {
            "id": source_id,
            "name": source_name,
            "type": data["type"],
            "enabled": bool(data.get("enabled", True)),
            "config": data.get("config", {}),
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
            "last_sync_at": "",
            "last_sync_status": "never",
            "last_error": "",
            "synced_files": 0,
            "local_cache_dir": self._cache_dir_for(source_id, source_name),
        }
        sources.append(source)
        self._save_registry(sources)
        return source

    def update_source(self, source_id: str, data: dict) -> dict:
        sources = self._load_registry()
        for index, source in enumerate(sources):
            if source["id"] != source_id:
                continue
            next_name = data.get("name", source["name"]).strip()
            next_type = data.get("type", source["type"])
            self._validate_source_payload({"name": next_name, "type": next_type})
            type_changed = next_type != source["type"]
            source["name"] = next_name
            source["type"] = next_type
            source["enabled"] = bool(data.get("enabled", source.get("enabled", True)))
            source["config"] = self._merge_config(source.get("config", {}), data.get("config"), type_changed)
            source["updated_at"] = _utc_now()
            source["local_cache_dir"] = source.get("local_cache_dir") or self._cache_dir_for(source["id"], source["name"])
            sources[index] = source
            self._save_registry(sources)
            return source
        raise KeyError(source_id)

    def delete_source(self, source_id: str):
        sources = self._load_registry()
        kept = []
        target = None
        for source in sources:
            if source["id"] == source_id:
                target = source
            else:
                kept.append(source)
        if target is None:
            raise KeyError(source_id)
        cache_dir = Path(target.get("local_cache_dir", ""))
        if cache_dir.exists():
            shutil.rmtree(cache_dir, ignore_errors=True)
        self._save_registry(kept)

    def _provider_for(self, source: dict) -> BaseMountProvider:
        provider_cls = self.PROVIDERS.get(source["type"])
        if provider_cls is None:
            raise ValueError(f"Unsupported source type: {source['type']}")
        return provider_cls(source)

    def _manifest_path(self, source: dict) -> Path:
        return Path(source["local_cache_dir"]) / ".manifest.json"

    def _load_manifest(self, source: dict) -> dict:
        manifest_path = self._manifest_path(source)
        if manifest_path.exists():
            try:
                return json.loads(manifest_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_manifest(self, source: dict, manifest: dict):
        manifest_path = self._manifest_path(source)
        _ensure_parent(manifest_path)
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def sync_source(self, source_id: str) -> dict:
        source = self.get_source(source_id)
        provider = self._provider_for(source)
        cache_dir = Path(source["local_cache_dir"])
        cache_dir.mkdir(parents=True, exist_ok=True)
        previous_manifest = self._load_manifest(source)
        remote_files = provider.list_files()
        remote_map = {item["rel_path"]: item for item in remote_files}

        downloaded = 0
        removed = 0
        new_manifest = {}

        for rel_path, file_info in remote_map.items():
            ext = Path(rel_path).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue
            dest_path = cache_dir / rel_path
            fingerprint = {
                "size": file_info.get("size"),
                "modified_at": file_info.get("modified_at"),
            }
            if previous_manifest.get(rel_path) != fingerprint or not dest_path.exists():
                provider.download(file_info, dest_path)
                downloaded += 1
            new_manifest[rel_path] = fingerprint

        for stale_rel in set(previous_manifest.keys()) - set(new_manifest.keys()):
            stale_path = cache_dir / stale_rel
            if stale_path.exists():
                stale_path.unlink()
                removed += 1

        self._save_manifest(source, new_manifest)
        sources = self._load_registry()
        updated = source
        for item in sources:
            if item["id"] != source_id:
                continue
            item["updated_at"] = _utc_now()
            item["last_sync_at"] = _utc_now()
            item["last_sync_status"] = "ok"
            item["last_error"] = ""
            item["synced_files"] = len(new_manifest)
            item["local_cache_dir"] = item.get("local_cache_dir") or self._cache_dir_for(item["id"], item["name"])
            updated = item
            break
        self._save_registry(sources)
        return {
            "source": updated,
            "downloaded": downloaded,
            "removed": removed,
            "total_files": len(new_manifest),
            "local_cache_dir": str(cache_dir),
        }

    def mark_sync_error(self, source_id: str, error: str):
        sources = self._load_registry()
        for item in sources:
            if item["id"] == source_id:
                item["last_sync_at"] = _utc_now()
                item["last_sync_status"] = "error"
                item["last_error"] = error
                break
        self._save_registry(sources)

    def sync_all_enabled(self) -> list[dict]:
        results = []
        for source in self._load_registry():
            if not source.get("enabled", True):
                continue
            try:
                results.append(self.sync_source(source["id"]))
            except Exception as exc:
                self.mark_sync_error(source["id"], str(exc))
                results.append({"source": source, "error": str(exc)})
        return results

    def collect_cache_dirs(self, source_ids: list[str] | None = None) -> list[Path]:
        sources = self._load_registry()
        selected = []
        wanted = set(source_ids or [])
        for source in sources:
            if source_ids and source["id"] not in wanted:
                continue
            if not source.get("enabled", True) and not source_ids:
                continue
            cache_dir = Path(source["local_cache_dir"])
            if cache_dir.exists():
                selected.append(cache_dir)
        return selected
