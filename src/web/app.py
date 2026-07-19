"""
Lumia ScriptorRAG FastAPI Web 应用 — 主入口文件。
提供 REST API:
  - POST /api/convert     上传 PDF 并执行 OCR
  - GET  /api/status/{id}  查询任务状态
  - GET  /api/result/{id}  获取转换结果
  - POST /api/providers    注册 LLM API Provider
  - GET  /api/providers    列出已注册 Provider
  - POST /api/providers/verify  验证所有 Provider 连接
"""
import os
import uuid
import json
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..llm import LLMRouter, APIKeyManager, APIKeyEntry
from ..llm.catalog import fetch_catalog
from ..formatter import MarkdownCleaner
from ..formatter.markdown_cleaner import MarkdownCleanOptions
from ..ingest import DocumentParser
from ..kb_mounts import KnowledgeMountManager
from ..rag import UniversalRAGEngine
from ..engines import (
    MinerUEngine, MarkerEngine, DoclingEngine,
    PaddleOCREngine, NougatEngine, SuryaEngine
)
from ..orchestrator import DocumentAnalyzer, OCRPipeline

logger = logging.getLogger(__name__)

app = FastAPI(title="Lumia ScriptorRAG", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
_default_data_root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Lumia ScriptorRAG"
UPLOAD_DIR = Path(os.environ.get("SCRIPTOR_RAG_UPLOAD_DIR", str(_default_data_root / "uploads")))
RAG_DB_DIR = Path(os.environ.get("SCRIPTOR_RAG_DB_DIR", str(_default_data_root / "rag_db")))
KB_MOUNT_DIR = Path(os.environ.get("SCRIPTOR_RAG_KB_MOUNT_DIR", str(_default_data_root / "kb_mounts")))
PROVIDER_STORE = Path(os.environ.get("SCRIPTOR_RAG_PROVIDER_STORE", str(_default_data_root / "providers.json")))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
RAG_DB_DIR.mkdir(parents=True, exist_ok=True)
KB_MOUNT_DIR.mkdir(parents=True, exist_ok=True)

tasks: dict[str, dict] = {}
llm_router = LLMRouter()
api_key_manager = APIKeyManager(PROVIDER_STORE)
analyzer = DocumentAnalyzer()
markdown_cleaner = MarkdownCleaner()
document_parser = DocumentParser()
rag_engine = UniversalRAGEngine(str(RAG_DB_DIR))
kb_mount_manager = KnowledgeMountManager(KB_MOUNT_DIR)
llm_router.hydrate(api_key_manager.all_entries())

# 引擎注册
ENGINE_CONFIG = {
    "mineru": {"gpu": True, "timeout": 300},
    "marker": {"gpu": True, "timeout": 300},
    "docling": {"gpu": True, "timeout": 300},
    "surya": {"gpu": True, "timeout": 300},
    "paddleocr": {"gpu": True, "lang": "ch", "timeout": 300},
    "nougat": {"gpu": True, "timeout": 600},
}

_engines = {}


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        bundle_root = getattr(sys, "_MEIPASS", None)
        if bundle_root:
            return Path(bundle_root).resolve()
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _resolve_asset_path(*parts: str) -> Path:
    return _runtime_root().joinpath(*parts)

def get_engines():
    if not _engines:
        engines = {
            "mineru": MinerUEngine(ENGINE_CONFIG["mineru"]),
            "marker": MarkerEngine(ENGINE_CONFIG["marker"]),
            "docling": DoclingEngine(ENGINE_CONFIG["docling"]),
            "surya": SuryaEngine(ENGINE_CONFIG["surya"]),
            "paddleocr": PaddleOCREngine(ENGINE_CONFIG["paddleocr"]),
            "nougat": NougatEngine(ENGINE_CONFIG["nougat"]),
        }
        _engines.update(engines)
    return _engines

# === API Models ===

class ProviderRegister(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str = ""
    route_group: str = "default"
    visible_provider: bool = False
    preferred_for: list[str] = []


class ProviderBootstrapRequest(BaseModel):
    providers: list[ProviderRegister]

class ConvertRequest(BaseModel):
    strategy: str = "auto"
    preferred_engine: str = ""

class MarkdownFormatRequest(BaseModel):
    markdown: str
    fix_headings: bool = True
    fix_lists: bool = True
    merge_paragraphs: bool = True
    remove_noise: bool = True
    normalize_punctuation: bool = True
    preserve_tables: bool = True

class RAGRebuildRequest(BaseModel):
    corpus_dir: str

class MountedRAGRebuildRequest(BaseModel):
    source_ids: list[str] = []
    sync_first: bool = True

class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 8
    use_llm: bool = True

class KBSourceCreateRequest(BaseModel):
    name: str
    type: str
    enabled: bool = True
    config: dict[str, Any] = {}

class KBSourceUpdateRequest(BaseModel):
    name: str | None = None
    type: str | None = None
    enabled: bool | None = None
    config: dict[str, Any] | None = None


SECRET_FIELD_HINTS = ("password", "token", "secret", "api_key", "access_key")


def _mask_secret(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    if len(text) <= 8:
        return "*" * len(text)
    return f"{text[:3]}{'*' * (len(text) - 6)}{text[-3:]}"


def _sanitize_source(source: dict) -> dict:
    safe = dict(source)
    config = {}
    for key, value in (safe.get("config") or {}).items():
        lower_key = key.lower()
        config[key] = _mask_secret(value) if any(hint in lower_key for hint in SECRET_FIELD_HINTS) else value
    safe["config"] = config
    return safe


def _merge_docs_from_dirs(cache_dirs: list[Path]) -> list[dict]:
    docs = []
    seen = set()
    for cache_dir in cache_dirs:
        for doc in document_parser.parse_directory(str(cache_dir)):
            key = (doc.get("title", ""), doc.get("content", "")[:180])
            if key in seen:
                continue
            seen.add(key)
            docs.append(doc)
    return docs

# === API Routes ===

@app.get("/api/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/api/engines")
async def list_engines():
    engines = get_engines()
    result = []
    for name, engine in engines.items():
        info = engine.get_metadata()
        try:
            info["available"] = await engine.is_available()
        except Exception as exc:
            info["available"] = False
            info["availability_error"] = str(exc)
        result.append({"name": name, **info})
    return {"engines": result}

@app.post("/api/format/markdown")
async def format_markdown(data: MarkdownFormatRequest):
    """独立字炉排版接口：清理 OCR 噪声并规范 Markdown。"""
    result = markdown_cleaner.clean_with_report(
        data.markdown,
        MarkdownCleanOptions(
            fix_headings=data.fix_headings,
            fix_lists=data.fix_lists,
            merge_paragraphs=data.merge_paragraphs,
            remove_noise=data.remove_noise,
            normalize_punctuation=data.normalize_punctuation,
            preserve_tables=data.preserve_tables,
        ),
    )
    return result

@app.post("/api/providers")
async def register_provider(data: ProviderRegister):
    """注册 LLM API Provider"""
    entry = APIKeyEntry(
        name=data.name,
        provider="",
        base_url=data.base_url,
        model=data.model,
        api_key=data.api_key,
        route_group=data.route_group,
        visible_provider=data.visible_provider,
        preferred_for=data.preferred_for,
    )
    provider = llm_router.register(
        data.name,
        data.base_url,
        data.api_key,
        data.model,
        route_group=data.route_group,
        preferred_for=data.preferred_for,
        visible_provider=data.visible_provider,
    )
    entry.provider = provider.config.provider
    api_key_manager.add_key(entry)
    return {"status": "registered", "name": data.name, "provider": provider.config.provider}


@app.post("/api/providers/bootstrap")
async def bootstrap_providers(data: ProviderBootstrapRequest):
    created = []
    for item in data.providers:
        entry = APIKeyEntry(
            name=item.name,
            provider="",
            base_url=item.base_url,
            model=item.model,
            api_key=item.api_key,
            route_group=item.route_group,
            visible_provider=item.visible_provider,
            preferred_for=item.preferred_for,
        )
        provider = llm_router.register(
            item.name,
            item.base_url,
            item.api_key,
            item.model,
            route_group=item.route_group,
            preferred_for=item.preferred_for,
            visible_provider=item.visible_provider,
        )
        entry.provider = provider.config.provider
        api_key_manager.add_key(entry)
        created.append({"name": item.name, "provider": provider.config.provider, "model": item.model})
    return {"status": "bootstrapped", "providers": created}

@app.get("/api/providers")
async def list_providers():
    providers = []
    for provider in llm_router.list_providers():
        sanitized = dict(provider)
        sanitized["base_url"] = ""
        providers.append(sanitized)
    keys = []
    for item in api_key_manager.list_keys():
        sanitized = dict(item)
        sanitized["base_url"] = ""
        keys.append(sanitized)
    return {"providers": providers, "keys": keys}

@app.get("/api/providers/catalog/{name}")
async def get_provider_catalog(name: str):
    entry = api_key_manager.get_key(name)
    if not entry:
        raise HTTPException(404, f"Provider not found: {name}")
    try:
        catalog = await fetch_catalog(entry.base_url, entry.api_key)
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "name": name,
        "base_url": "",
        "model": entry.model,
        "route_group": entry.route_group,
        "preferred_for": entry.preferred_for,
        **catalog,
    }

@app.post("/api/providers/delete/{name}")
async def delete_provider(name: str):
    llm_router.remove(name)
    api_key_manager.remove_key(name)
    return {"status": "deleted", "name": name}

@app.post("/api/providers/verify")
async def verify_providers():
    results = await llm_router.verify_all()
    return {"results": results}

@app.post("/api/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    strategy: str = Form("auto"),
    preferred_engine: str = Form(""),
):
    """上传 PDF 并启动 OCR 转换"""
    task_id = str(uuid.uuid4())
    ext = Path(file.filename).suffix if file.filename else ".pdf"
    save_path = UPLOAD_DIR / f"{task_id}{ext}"

    content = await file.read()
    save_path.write_bytes(content)

    tasks[task_id] = {
        "id": task_id,
        "filename": file.filename,
        "status": "queued",
        "progress": 0,
        "created_at": datetime.now().isoformat(),
    }

    asyncio.create_task(_run_conversion(task_id, str(save_path), strategy, preferred_engine))
    return {"task_id": task_id, "status": "queued"}

@app.get("/api/status/{task_id}")
async def get_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task

@app.get("/api/result/{task_id}")
async def get_result(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    if task["status"] != "completed":
        raise HTTPException(400, f"Task not completed, current status: {task['status']}")
    return task

@app.get("/api/download/{task_id}")
async def download_result(task_id: str):
    task = tasks.get(task_id)
    if not task or task["status"] != "completed":
        raise HTTPException(404, "Result not available")
    result_path = UPLOAD_DIR / f"{task_id}_result.md"
    result_path.write_text(task.get("markdown", ""), encoding="utf-8")
    return FileResponse(str(result_path), filename=f"{Path(task['filename']).stem}.md", media_type="text/markdown")

@app.get("/api/kb-sources")
async def list_kb_sources():
    sources = kb_mount_manager.list_sources()
    return {
        "sources": [_sanitize_source(source) for source in sources],
        "supported_types": [
            {
                "type": "local_dir",
                "label": "本地目录",
                "fields": ["root_path"],
                "description": "直接挂载本机已整理好的知识库目录。",
            },
            {
                "type": "webdav",
                "label": "WebDAV",
                "fields": ["base_url", "root_path", "username", "password"],
                "description": "兼容坚果云、Nextcloud、群晖等标准 WebDAV 服务。",
            },
            {
                "type": "alist",
                "label": "AList",
                "fields": ["base_url", "root_path", "token", "password"],
                "description": "兼容 AList 聚合云盘，适合统一挂载多个远程盘。",
            },
        ],
    }

@app.post("/api/kb-sources")
async def create_kb_source(data: KBSourceCreateRequest):
    try:
        source = kb_mount_manager.add_source(data.model_dump())
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"status": "created", "source": _sanitize_source(source)}

@app.put("/api/kb-sources/{source_id}")
async def update_kb_source(source_id: str, data: KBSourceUpdateRequest):
    payload = {key: value for key, value in data.model_dump().items() if value is not None}
    try:
        source = kb_mount_manager.update_source(source_id, payload)
    except KeyError as exc:
        raise HTTPException(404, f"Knowledge source not found: {source_id}") from exc
    except Exception as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"status": "updated", "source": _sanitize_source(source)}

@app.delete("/api/kb-sources/{source_id}")
async def delete_kb_source(source_id: str):
    try:
        kb_mount_manager.delete_source(source_id)
    except KeyError as exc:
        raise HTTPException(404, f"Knowledge source not found: {source_id}") from exc
    return {"status": "deleted", "id": source_id}

@app.post("/api/kb-sources/{source_id}/sync")
async def sync_kb_source(source_id: str):
    try:
        result = kb_mount_manager.sync_source(source_id)
        result["source"] = _sanitize_source(result["source"])
        return {"status": "synced", **result}
    except KeyError as exc:
        raise HTTPException(404, f"Knowledge source not found: {source_id}") from exc
    except Exception as exc:
        kb_mount_manager.mark_sync_error(source_id, str(exc))
        raise HTTPException(400, str(exc)) from exc

@app.post("/api/kb-sources/sync-all")
async def sync_all_kb_sources():
    results = kb_mount_manager.sync_all_enabled()
    normalized = []
    for item in results:
        normalized.append(
            {
                **item,
                "source": _sanitize_source(item.get("source", {})),
            }
        )
    return {"status": "completed", "results": normalized}

@app.get("/api/rag/status")
async def rag_status():
    """查看当前文枢 RAG 索引状态。"""
    return {"status": "ok", **rag_engine.stats()}

@app.post("/api/rag/rebuild")
async def rebuild_rag(data: RAGRebuildRequest):
    """从已清洗文档目录重建文枢 RAG 索引。支持 md/txt/html/pdf/epub/docx。"""
    corpus_dir = Path(data.corpus_dir).expanduser()
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        raise HTTPException(400, f"Corpus directory not found: {data.corpus_dir}")
    docs = document_parser.parse_directory(str(corpus_dir))
    if not docs:
        raise HTTPException(400, "No supported documents found in corpus directory")
    stats = rag_engine.index_documents(docs)
    return {"status": "rebuilt", "corpus_dir": str(corpus_dir), **stats}

@app.post("/api/rag/rebuild-mounted")
async def rebuild_rag_from_mounted(data: MountedRAGRebuildRequest):
    sync_results = []
    if data.sync_first:
        if not data.source_ids:
            sync_results = []
            for item in kb_mount_manager.sync_all_enabled():
                sync_results.append({**item, "source": _sanitize_source(item.get("source", {}))})
        else:
            sync_results = [await sync_kb_source(source_id) for source_id in data.source_ids]
    cache_dirs = kb_mount_manager.collect_cache_dirs(data.source_ids or None)
    if not cache_dirs:
        raise HTTPException(400, "No mounted knowledge source cache found. Please sync a source first.")
    docs = _merge_docs_from_dirs(cache_dirs)
    if not docs:
        raise HTTPException(400, "Mounted sources do not contain supported documents.")
    stats = rag_engine.index_documents(docs)
    return {
        "status": "rebuilt",
        "mode": "mounted_sources",
        "cache_dirs": [str(path) for path in cache_dirs],
        "source_ids": data.source_ids,
        "sync_results": sync_results,
        **stats,
    }

@app.post("/api/rag/query")
async def query_rag(data: RAGQueryRequest):
    """文枢 RAG 问答：先返回至少 5 个不同文档来源，再可选调用 LLM 综合。"""
    refs = rag_engine.retrieve(data.question, data.top_k)
    answer = ""
    if data.use_llm and llm_router.list_providers() and refs:
        context = "\n\n---\n\n".join(
            f"[文献{i + 1}] 《{ref.get('title', '')}》\n{ref.get('content', '')}"
            for i, ref in enumerate(refs)
        )
        prompt = (
            "请基于以下本地资料回答用户问题。必须优先引用资料，不要编造；"
            "如果资料不足，请明确说明。\n\n"
            f"用户问题：{data.question}\n\n参考资料：\n{context}"
        )
        try:
            answer = await llm_router.route("rag_answer", [{"role": "user", "content": prompt}])
        except Exception as exc:
            logger.warning("RAG LLM answer failed, falling back: %s", exc)
    if not answer:
        answer = rag_engine.fallback_answer(refs)
    return {"answer": answer, "references": refs, "stats": rag_engine.stats()}

async def _run_conversion(task_id: str, pdf_path: str, strategy: str, preferred_engine: str):
    try:
        tasks[task_id]["status"] = "analyzing"
        tasks[task_id]["progress"] = 10
        analysis = await analyzer.analyze(pdf_path)
        tasks[task_id]["analysis"] = analysis
        tasks[task_id]["progress"] = 20
        if not preferred_engine:
            preferred_engine = analysis.get("recommended_engine", "")

        tasks[task_id]["status"] = "converting"
        pipeline = OCRPipeline(get_engines(), llm_router if llm_router.list_providers() else None)
        result = await pipeline.run(pdf_path, strategy, preferred_engine)
        tasks[task_id].update(result)
        tasks[task_id]["progress"] = 100
        tasks[task_id]["status"] = "completed"
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["progress"] = 0
        logger.exception(f"Task {task_id} failed")

@app.get("/", response_class=HTMLResponse)
async def index():
    """提供静态前端页面"""
    index_path = _resolve_asset_path("frontend", "dist", "index.html")
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Lumia ScriptorRAG API</h1><p>Frontend not built. Run <code>cd frontend && npm install && npm run build</code></p>")

dist_path = _resolve_asset_path("frontend", "dist")
assets_path = dist_path / "assets"
if assets_path.exists():
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")

favicon_path = dist_path / "favicon.svg"
if favicon_path.exists():
    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(str(favicon_path), media_type="image/svg+xml")

@app.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_fallback(full_path: str):
    """Vue history 路由兜底，避免刷新 /rag、/format 或误粘路径时返回 404。"""
    if full_path.startswith("api/"):
        raise HTTPException(404, "API route not found")
    return await index()

def run():
    import uvicorn
    host = os.environ.get("SCRIPTOR_RAG_HOST", os.environ.get("OCR_HARNESS_HOST", "0.0.0.0"))
    port = int(os.environ.get("SCRIPTOR_RAG_PORT", os.environ.get("OCR_HARNESS_PORT", "8080")))
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=not getattr(sys, "frozen", False),
        log_config=None,
        access_log=False,
    )
