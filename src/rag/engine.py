import os
import pickle
import re
from pathlib import Path

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
CLASSIC_HINTS = (
    "黄帝内经", "素问", "灵枢", "难经", "伤寒", "金匮", "脉经", "脾胃论", "温病条辨",
    "本草纲目", "妇人大全良方", "傅青主", "临证指南医案", "医宗金鉴", "论语", "孟子",
    "大学", "中庸", "道德经", "庄子", "周易", "诗经", "尚书", "礼记",
)
MODERN_HINTS = ("讲记", "讲读", "图解", "养生", "研究", "解读", "诠解", "浅说", "扫描版", "z-library")


class UniversalRAGEngine:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.chunks = []
        self.bm25 = None
        self._load()

    def _tokenize(self, text: str) -> list[str]:
        if jieba:
            return list(jieba.cut(text))
        return re.findall(r"[\w\u4e00-\u9fff]+", text)

    def _normalize_title(self, title: str, source: str = "") -> str:
        text = str(title or "").strip() or Path(source).stem
        text = ENGINE_TAG_PAT.sub("", text).replace("__", " ").replace("_", " ").strip(" -")
        return text or "未知文档"

    def _source_key(self, title: str, source: str = "") -> str:
        text = self._normalize_title(title, source)
        text = re.sub(r"\s+", "", text)
        text = re.sub(r"[\[\]【】《》“”\"'（）()·._-]", "", text)
        text = re.sub(r"(第[一二三四五六七八九十\d]+册|上册|下册|全本|副本)$", "", text)
        return text[:60] or self._normalize_title(title, source)

    def _source_tier(self, title: str, source: str = "") -> str:
        text = f"{title} {source}"
        if any(hint in text for hint in MODERN_HINTS):
            return "modern"
        if any(hint in text for hint in CLASSIC_HINTS):
            return "classic"
        return "commentary"

    def _tier_boost(self, tier: str) -> float:
        return {"classic": 0.18, "commentary": 0.08, "modern": 0.0}.get(tier, 0.0)

    def _chunk(self, text: str, max_len: int = 800) -> list[str]:
        paragraphs = text.split("\n\n")
        chunks, buffer = [], ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(buffer) + len(para) < max_len:
                buffer += para + "\n\n"
            else:
                if buffer:
                    chunks.append(buffer.strip())
                buffer = para + "\n\n"
        if buffer:
            chunks.append(buffer.strip())
        return chunks

    def _extract_chapter(self, content: str) -> str:
        for line in content.strip().split("\n")[:8]:
            line = line.strip()
            match = re.search(r"(第[一二三四五六七八九十百千\d]+[品章节篇卷])", line)
            if match:
                return line[max(0, match.start() - 8): min(len(line), match.end() + 12)].strip()
            if 2 < len(line) < 50 and not line.startswith("【"):
                return line
        return ""

    def index_documents(self, docs: list[dict]) -> dict:
        self.chunks = []
        seen = set()
        for doc in docs:
            source = doc.get("source", "")
            title = self._normalize_title(doc.get("title", ""), source)
            chapter = self._extract_chapter(doc.get("content", ""))
            for chunk in self._chunk(doc.get("content", "")):
                key = (title, chunk[:180])
                if key in seen:
                    continue
                seen.add(key)
                tier = self._source_tier(title, source)
                self.chunks.append({
                    "content": chunk,
                    "source": source,
                    "title": title,
                    "chapter": self._extract_chapter(chunk) or chapter,
                    "source_key": self._source_key(title, source),
                    "source_tier": tier,
                })
        tokenized = [self._tokenize(item["content"]) for item in self.chunks]
        self.bm25 = BM25Okapi(tokenized) if BM25Okapi and tokenized else None
        self._save()
        return {"chunks": len(self.chunks), "documents": len({c["source_key"] for c in self.chunks})}

    def retrieve(self, query: str, top_k: int = 8) -> list[dict]:
        top_k = max(top_k, MIN_REFERENCE_DOCS)
        if not self.chunks:
            return []
        tokens = self._tokenize(query)
        if self.bm25 and np is not None:
            scores = self.bm25.get_scores(tokens)
            max_score = float(np.max(scores)) if len(scores) else 0.0
            candidate_ids = np.argsort(scores)[-min(len(self.chunks), max(top_k * 40, 200)):][::-1]
            ranked = []
            for idx in candidate_ids:
                chunk = self.chunks[int(idx)]
                raw = float(scores[int(idx)]) / max_score if max_score > 0 else 0.0
                ranked.append((raw + self._tier_boost(chunk.get("source_tier", "")), raw, int(idx), chunk))
        else:
            query_terms = set(tokens)
            ranked = []
            for idx, chunk in enumerate(self.chunks):
                content_terms = set(self._tokenize(chunk["content"]))
                raw = len(query_terms & content_terms) / max(len(query_terms), 1)
                ranked.append((raw + self._tier_boost(chunk.get("source_tier", "")), raw, idx, chunk))
        ranked.sort(key=lambda item: item[0], reverse=True)
        seen_docs, seen_content, results = set(), set(), []
        for final_score, raw_score, _, chunk in ranked:
            doc_key = chunk.get("source_key") or self._source_key(chunk.get("title", ""), chunk.get("source", ""))
            content_key = chunk["content"][:100]
            if doc_key in seen_docs or content_key in seen_content:
                continue
            seen_docs.add(doc_key)
            seen_content.add(content_key)
            item = dict(chunk)
            item["score"] = round(final_score, 4)
            item["raw_score"] = round(raw_score, 4)
            results.append(item)
            if len(results) >= top_k:
                break
        return results

    def fallback_answer(self, refs: list[dict]) -> str:
        if not refs:
            return "一句话精要\n当前索引中没有检索到足够相关的内容。"
        lines = ["一句话精要", "已从本地知识库检索到相关内容，以下按相关度列出可追溯出处。", "", "检索依据"]
        for ref in refs[:MIN_REFERENCE_DOCS]:
            title = self._normalize_title(ref.get("title", ""), ref.get("source", ""))
            chapter = ref.get("chapter", "")
            cite = f"《{title}》" + (f"·{chapter}" if chapter else "")
            excerpt = re.sub(r"\s+", " ", ref.get("content", "")).strip()[:260]
            lines.extend([f"- 出处：{cite}", f"  摘要：{excerpt}"])
        return "\n".join(lines).strip()

    def _save(self):
        with (self.db_path / "chunks.pkl").open("wb") as f:
            pickle.dump(self.chunks, f)
        with (self.db_path / "bm25.pkl").open("wb") as f:
            pickle.dump(self.bm25, f)

    def _load(self):
        chunks_path = self.db_path / "chunks.pkl"
        bm25_path = self.db_path / "bm25.pkl"
        if chunks_path.exists():
            with chunks_path.open("rb") as f:
                self.chunks = pickle.load(f)
        if bm25_path.exists():
            with bm25_path.open("rb") as f:
                self.bm25 = pickle.load(f)

    def stats(self) -> dict:
        return {
            "chunks": len(self.chunks),
            "documents": len({c.get("source_key") for c in self.chunks}),
            "db_path": str(self.db_path),
        }
