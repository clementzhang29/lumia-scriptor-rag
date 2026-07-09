import os
import re
from pathlib import Path

ENGINE_TAG_PAT = re.compile(r"_(docling|mineru|surya|marker|paddleocr)$", re.I)
SYMBOL_ONLY_PAT = re.compile(r"^[\s\-\+\*_=|/\\.·:：'‘’\[\](){}<>?？!！,，;；`~@#$%^&]+$")
WATERMARK_PAT = re.compile(r"A-PDF MERGER DEMO|a-pdf\.com", re.I)
ALLOWED_EXTS = {".epub", ".pdf", ".txt", ".md", ".html", ".htm", ".docx"}
ENGINE_PRIORITY = {"docling": 5, "surya": 4, "mineru": 3, "marker": 2, "paddleocr": 1}


class DocumentParser:
    def _canonical_stem(self, fname: str) -> str:
        stem = os.path.splitext(fname)[0]
        stem = ENGINE_TAG_PAT.sub("", stem)
        stem = re.sub(r"\.pdf$", "", stem, flags=re.I)
        stem = re.sub(r"([ _-])1$", "", stem)
        return stem.replace("__", " ").replace("_", " ").strip().lower()

    def _file_priority(self, fname: str) -> tuple[int, int]:
        lower = fname.lower()
        engine_match = re.search(r"_(docling|mineru|surya|marker|paddleocr)\.(md|txt)$", lower)
        engine_score = ENGINE_PRIORITY.get(engine_match.group(1), 0) if engine_match else 0
        ext = os.path.splitext(lower)[1]
        ext_score = {".md": 4, ".txt": 3, ".html": 2, ".htm": 2, ".docx": 1, ".pdf": 0, ".epub": 0}.get(ext, 0)
        penalty = -10 if re.search(r"_1_(docling|mineru|surya|marker|paddleocr)\.(md|txt)$", lower) else 0
        if penalty == 0:
            penalty = -1 if re.search(r"([ _-])1(\.[^.]+)+$", lower) else 0
        return engine_score, ext_score + penalty

    def parse(self, filepath: str) -> list[dict]:
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".epub":
            return self._parse_epub(filepath)
        if ext == ".pdf":
            return self._parse_pdf(filepath)
        if ext in (".txt", ".md"):
            return self._parse_text(filepath)
        if ext in (".html", ".htm"):
            return self._parse_html(filepath)
        if ext == ".docx":
            return self._parse_docx(filepath)
        raise ValueError(f"Unsupported format: {ext}")

    def _normalize_title(self, path: str, text: str) -> str:
        stem = ENGINE_TAG_PAT.sub("", Path(path).stem).replace("__", " ").replace("_", " ").strip()
        first_line = text.split("\n", 1)[0].strip() if text else ""
        if first_line.startswith("# "):
            return first_line[2:].strip()
        if first_line.startswith("## "):
            return first_line[3:].strip()
        return stem or Path(path).name

    def _clean_text(self, text: str) -> str:
        text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
        lines = []
        for raw in text.split("\n"):
            line = raw.strip()
            if not line:
                lines.append("")
                continue
            if "<!-- image -->" in line or WATERMARK_PAT.search(line) or SYMBOL_ONLY_PAT.fullmatch(line):
                continue
            if line.startswith("# # "):
                lines.append("## " + line[4:].strip())
                continue
            lines.append(raw.rstrip())
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        return text.strip()

    def _parse_text(self, path: str) -> list[dict]:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        text = self._clean_text(text)
        return [{"title": self._normalize_title(path, text), "content": text, "source": os.path.basename(path)}] if text else []

    def _parse_html(self, path: str) -> list[dict]:
        from bs4 import BeautifulSoup

        html = Path(path).read_text(encoding="utf-8", errors="ignore")
        text = self._clean_text(BeautifulSoup(html, "html.parser").get_text("\n"))
        return [{"title": self._normalize_title(path, text), "content": text, "source": os.path.basename(path)}] if text else []

    def _parse_docx(self, path: str) -> list[dict]:
        import docx

        doc = docx.Document(path)
        text = self._clean_text("\n".join(p.text for p in doc.paragraphs))
        return [{"title": self._normalize_title(path, text), "content": text, "source": os.path.basename(path)}] if text else []

    def _parse_epub(self, path: str) -> list[dict]:
        from bs4 import BeautifulSoup
        from ebooklib import ITEM_DOCUMENT, epub

        book = epub.read_epub(path)
        meta_title = book.get_metadata("DC", "title")
        title = meta_title[0][0] if meta_title else Path(path).stem
        docs = []
        for item in book.get_items_of_type(ITEM_DOCUMENT):
            html = item.get_content().decode("utf-8", errors="ignore")
            text = self._clean_text(BeautifulSoup(html, "html.parser").get_text("\n"))
            if len(text) > 50:
                docs.append({"title": title, "content": text, "source": os.path.basename(path)})
        return docs

    def _parse_pdf(self, path: str) -> list[dict]:
        import fitz

        pdf = fitz.open(path)
        title = pdf.metadata.get("title", "") or Path(path).stem
        pages = []
        for page in pdf:
            text = self._clean_text(page.get_text().strip())
            if text:
                pages.append({"title": title, "content": text, "source": os.path.basename(path), "page": page.number + 1})
        pdf.close()
        return pages

    def parse_directory(self, dirpath: str) -> list[dict]:
        selected = {}
        seen = set()
        docs = []
        for root, _, files in os.walk(dirpath):
            if any(part in {"node_modules", ".git", "__pycache__", "dist", "build"} for part in Path(root).parts):
                continue
            for fname in files:
                if os.path.splitext(fname)[1].lower() not in ALLOWED_EXTS:
                    continue
                lower_name = fname.lower()
                if re.search(r"_1_(docling|mineru|surya|marker|paddleocr)\.", lower_name):
                    continue
                fp = os.path.join(root, fname)
                key = os.path.join(root, self._canonical_stem(fname))
                current = (self._file_priority(fname), fp)
                if key not in selected or current[0] > selected[key][0]:
                    selected[key] = current
        for _, fp in selected.values():
            try:
                for doc in self.parse(fp):
                    key = (doc.get("title", ""), doc.get("content", "")[:180])
                    if key in seen:
                        continue
                    seen.add(key)
                    docs.append(doc)
            except Exception:
                continue
        return docs
