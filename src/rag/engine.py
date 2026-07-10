from __future__ import annotations

import hashlib
import json
import pickle
import re
import sqlite3
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import jieba
except Exception:
    jieba = None

try:
    import numpy as np
except Exception:
    np = None

try:
    from rank_bm25 import BM25Okapi
except Exception:
    BM25Okapi = None

ENGINE_TAG_PAT = re.compile(r"_(docling|mineru|surya|marker|paddleocr)$", re.I)
MIN_REFERENCE_DOCS = 5
DEFAULT_CHUNK_SIZE = 850
DEFAULT_CHUNK_OVERLAP = 120

CLASSIC_HINTS = (
    "黄帝内经",
    "素问",
    "灵枢",
    "难经",
    "伤寒",
    "金匮",
    "脉经",
    "本草纲目",
    "傅青主",
    "临证指南医案",
    "医宗金鉴",
    "论语",
    "孟子",
    "大学",
    "中庸",
    "道德经",
    "庄子",
    "周易",
    "诗经",
    "尚书",
    "礼记",
)
MODERN_HINTS = ("讲记", "解读", "图解", "养生", "研究", "浅说", "扫瞄", "z-library")


class UniversalRAGEngine:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.sqlite_path = self.db_path / "rag.sqlite3"
        self._conn = sqlite3.connect(self.sqlite_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()
        self.documents: list[dict[str, Any]] = []
        self.chunks: list[dict[str, Any]] = []
        self.bm25 = None
        self._load()

    def close(self) -> None:
        if getattr(self, "_conn", None) is not None:
            self._conn.close()
            self._conn = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _ensure_schema(self) -> None:
        cur = self._conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                source_tier TEXT NOT NULL,
                chunk_count INTEGER NOT NULL DEFAULT 0,
                token_count INTEGER NOT NULL DEFAULT 0,
                created_at REAL NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_key TEXT NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                source_tier TEXT NOT NULL,
                chapter TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                token_count INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(doc_key) REFERENCES documents(doc_key)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_key ON chunks(doc_key)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_title ON chunks(title)")
        self._conn.commit()

    def _tokenize(self, text: str) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text or "").strip()
        if not cleaned:
            return []
        if jieba:
            return [token.strip() for token in jieba.cut(cleaned) if token.strip()]
        return re.findall(r"[\w\u4e00-\u9fff]+", cleaned)

    def _normalize_title(self, title: str, source: str = "") -> str:
        text = str(title or "").strip() or Path(source).stem
        text = ENGINE_TAG_PAT.sub("", text).replace("__", " ").replace("_", " ").strip(" -")
        return text or "未知文档"

    def _normalize_text(self, text: str) -> str:
        text = (text or "").replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _source_key(self, title: str, source: str = "") -> str:
        raw = self._normalize_title(title, source)
        normalized = re.sub(r"\s+", "", raw)
        normalized = re.sub(r"[\[\]【】《》<>（）()·._\-\s]", "", normalized)
        normalized = normalized[:80] or raw
        return normalized.lower()

    def _source_tier(self, title: str, source: str = "") -> str:
        text = f"{title} {source}"
        if any(hint in text for hint in CLASSIC_HINTS):
            return "classic"
        if any(hint in text for hint in MODERN_HINTS):
            return "modern"
        return "commentary"

    def _tier_boost(self, tier: str) -> float:
        return {"classic": 0.22, "commentary": 0.08, "modern": 0.0}.get(tier, 0.0)

    def _extract_chapter(self, content: str) -> str:
        for line in (content or "").splitlines()[:8]:
            line = line.strip()
            if not line:
                continue
            if 2 < len(line) < 60 and not line.startswith(("#", "-", "*", "•")):
                return line
        return ""

    def _chunk(self, text: str, max_len: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[str]:
        text = self._normalize_text(text)
        if not text:
            return []
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        chunks: list[str] = []
        buffer = ""
        for para in paragraphs:
            if not buffer:
                buffer = para
                continue
            if len(buffer) + len(para) + 2 <= max_len:
                buffer += "\n\n" + para
                continue
            chunks.append(buffer.strip())
            tail = buffer[-overlap:] if overlap > 0 else ""
            buffer = (tail + "\n\n" + para).strip()
        if buffer:
            chunks.append(buffer.strip())
        return [chunk for chunk in chunks if len(chunk) > 12]

    def _hash_content(self, text: str) -> str:
        return hashlib.sha1((text or "").encode("utf-8", errors="ignore")).hexdigest()

    def _document_priority(self, title: str, source: str) -> float:
        tier = self._source_tier(title, source)
        return self._tier_boost(tier)

    def _prepare_documents(self, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        prepared = []
        seen_doc_keys: set[str] = set()
        for doc in docs:
            source = str(doc.get("source", "") or "")
            title = self._normalize_title(doc.get("title", ""), source)
            doc_key = self._source_key(title, source)
            if doc_key in seen_doc_keys:
                continue
            seen_doc_keys.add(doc_key)
            content = self._normalize_text(doc.get("content", ""))
            if not content:
                continue
            prepared.append(
                {
                    "doc_key": doc_key,
                    "title": title,
                    "source": source,
                    "source_tier": self._source_tier(title, source),
                    "chapter": self._extract_chapter(content),
                    "content": content,
                }
            )
        return prepared

    def index_documents(self, docs: list[dict[str, Any]]) -> dict[str, Any]:
        prepared_docs = self._prepare_documents(docs)
        if not prepared_docs:
            self.chunks = []
            self.documents = []
            self.bm25 = None
            self._persist_empty()
            return {"chunks": 0, "documents": 0}

        cur = self._conn.cursor()
        cur.execute("DELETE FROM chunks")
        cur.execute("DELETE FROM documents")

        all_chunks: list[dict[str, Any]] = []
        now = time.time()
        for doc in prepared_docs:
            chunk_texts = self._chunk(doc["content"])
            cur.execute(
                """
                INSERT OR REPLACE INTO documents
                (doc_key, title, source, source_tier, chunk_count, token_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc["doc_key"],
                    doc["title"],
                    doc["source"],
                    doc["source_tier"],
                    len(chunk_texts),
                    len(self._tokenize(doc["content"])),
                    now,
                ),
            )
            for position, chunk in enumerate(chunk_texts):
                chunk_record = {
                    "doc_key": doc["doc_key"],
                    "title": doc["title"],
                    "source": doc["source"],
                    "source_tier": doc["source_tier"],
                    "chapter": self._extract_chapter(chunk) or doc["chapter"],
                    "position": position,
                    "content": chunk,
                    "content_hash": self._hash_content(chunk),
                    "token_count": len(self._tokenize(chunk)),
                }
                cur.execute(
                    """
                    INSERT INTO chunks
                    (doc_key, title, source, source_tier, chapter, position, content, content_hash, token_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_record["doc_key"],
                        chunk_record["title"],
                        chunk_record["source"],
                        chunk_record["source_tier"],
                        chunk_record["chapter"],
                        chunk_record["position"],
                        chunk_record["content"],
                        chunk_record["content_hash"],
                        chunk_record["token_count"],
                    ),
                )
                chunk_record["chunk_id"] = cur.lastrowid
                all_chunks.append(chunk_record)

        self._conn.commit()
        self.documents = prepared_docs
        self.chunks = all_chunks
        self._build_bm25()
        self._save_cache()
        return {"chunks": len(self.chunks), "documents": len(self.documents)}

    def _build_bm25(self) -> None:
        tokenized = [self._tokenize(item["content"]) for item in self.chunks]
        self.bm25 = BM25Okapi(tokenized) if BM25Okapi and tokenized else None

    def _load(self) -> None:
        cur = self._conn.cursor()
        cur.execute("SELECT doc_key, title, source, source_tier, chunk_count, token_count, created_at FROM documents ORDER BY title")
        self.documents = [dict(row) for row in cur.fetchall()]
        cur.execute(
            """
            SELECT chunk_id, doc_key, title, source, source_tier, chapter, position, content, content_hash, token_count
            FROM chunks
            ORDER BY doc_key, position, chunk_id
            """
        )
        self.chunks = [dict(row) for row in cur.fetchall()]
        if not self.chunks:
            self.bm25 = None
            return
        bm25_path = self.db_path / "bm25.pkl"
        if bm25_path.exists():
            try:
                with bm25_path.open("rb") as f:
                    self.bm25 = pickle.load(f)
                    return
            except Exception:
                pass
        self._build_bm25()

    def _save_cache(self) -> None:
        with (self.db_path / "chunks.pkl").open("wb") as f:
            pickle.dump(self.chunks, f)
        with (self.db_path / "bm25.pkl").open("wb") as f:
            pickle.dump(self.bm25, f)

    def _persist_empty(self) -> None:
        for name in ("chunks.pkl", "bm25.pkl"):
            path = self.db_path / name
            if path.exists():
                path.unlink()

    def _score_chunk(self, query_tokens: list[str], chunk: dict[str, Any]) -> tuple[float, float]:
        if self.bm25 and np is not None and self.chunks:
            idx = chunk.get("_idx", 0)
            scores = self.bm25.get_scores(query_tokens)
            raw = float(scores[idx])
            max_score = float(np.max(scores)) if len(scores) else 0.0
            base = raw / max_score if max_score > 0 else 0.0
        else:
            query_terms = Counter(query_tokens)
            content_terms = Counter(self._tokenize(chunk["content"]))
            overlap = sum(min(query_terms[token], content_terms[token]) for token in query_terms)
            base = overlap / max(sum(query_terms.values()), 1)
            raw = base
        doc_boost = self._tier_boost(chunk.get("source_tier", ""))
        length_boost = min(len(chunk.get("content", "")) / 2400.0, 0.08)
        return base + doc_boost + length_boost, raw

    def retrieve(self, query: str, top_k: int = 8) -> list[dict[str, Any]]:
        top_k = max(int(top_k or 0), MIN_REFERENCE_DOCS)
        if not self.chunks:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            query_tokens = self._tokenize(" ".join(query.split()))

        scored: list[tuple[float, float, dict[str, Any]]] = []
        for idx, chunk in enumerate(self.chunks):
            item = dict(chunk)
            item["_idx"] = idx
            final_score, raw_score = self._score_chunk(query_tokens, item)
            scored.append((final_score, raw_score, item))

        scored.sort(key=lambda row: row[0], reverse=True)

        doc_counts: defaultdict[str, int] = defaultdict(int)
        used_hashes: set[str] = set()
        results: list[dict[str, Any]] = []
        per_doc_limit = 2 if len(self.documents) >= 20 else 3
        source_floor = max(MIN_REFERENCE_DOCS, min(top_k, 12))

        for final_score, raw_score, chunk in scored:
            doc_key = chunk.get("doc_key") or self._source_key(chunk.get("title", ""), chunk.get("source", ""))
            content_hash = chunk.get("content_hash") or self._hash_content(chunk.get("content", ""))
            if content_hash in used_hashes:
                continue
            if doc_counts[doc_key] >= per_doc_limit:
                continue

            item = dict(chunk)
            item.pop("_idx", None)
            item["score"] = round(final_score, 4)
            item["raw_score"] = round(raw_score, 4)
            item["source_key"] = doc_key
            results.append(item)
            used_hashes.add(content_hash)
            doc_counts[doc_key] += 1
            if len(results) >= top_k and len(doc_counts) >= source_floor:
                break

        if len(results) < MIN_REFERENCE_DOCS:
            for final_score, raw_score, chunk in scored:
                doc_key = chunk.get("doc_key") or self._source_key(chunk.get("title", ""), chunk.get("source", ""))
                content_hash = chunk.get("content_hash") or self._hash_content(chunk.get("content", ""))
                if content_hash in used_hashes:
                    continue
                item = dict(chunk)
                item.pop("_idx", None)
                item["score"] = round(final_score, 4)
                item["raw_score"] = round(raw_score, 4)
                item["source_key"] = doc_key
                results.append(item)
                used_hashes.add(content_hash)
                if len(results) >= MIN_REFERENCE_DOCS:
                    break

        return results[:top_k]

    def fallback_answer(self, refs: list[dict[str, Any]]) -> str:
        if not refs:
            return "当前索引中没有检索到足够相关的内容。"
        lines = [
            "简要结论",
            "已从本地知识库检索到相关内容，下面列出可追溯出处。",
            "",
            "检索依据",
        ]
        for ref in refs[:MIN_REFERENCE_DOCS]:
            title = self._normalize_title(ref.get("title", ""), ref.get("source", ""))
            chapter = ref.get("chapter", "")
            cite = f"《{title}》" + (f" · {chapter}" if chapter else "")
            excerpt = re.sub(r"\s+", " ", ref.get("content", "")).strip()[:260]
            lines.extend([f"- 出处：{cite}", f"  摘要：{excerpt}"])
        return "\n".join(lines).strip()

    def stats(self) -> dict[str, Any]:
        return {
            "chunks": len(self.chunks),
            "documents": len(self.documents),
            "db_path": str(self.db_path),
            "sqlite_path": str(self.sqlite_path),
            "bm25_ready": bool(self.bm25),
        }
