from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


def extract_pdf_text_with_fitz(pdf_path: str) -> str:
    import fitz

    doc = fitz.open(pdf_path)
    try:
        pages: list[str] = []
        for page in doc:
            blocks = page.get_text("blocks")
            lines = [
                block[4].strip()
                for block in sorted(blocks, key=lambda item: (round(item[1], 1), round(item[0], 1)))
                if block[4].strip()
            ]
            if not lines:
                lines = [page.get_text("text").strip()]
            page_text = "\n".join(line for line in lines if line)
            if page_text.strip():
                pages.append(page_text)
        return "\n\n".join(pages).strip()
    finally:
        doc.close()


@dataclass
class OCRResult:
    markdown: str = ""
    json_data: Optional[dict] = None
    metadata: dict = field(default_factory=dict)
    pages: list[dict] = field(default_factory=list)
    success: bool = True
    error: Optional[str] = None
    engine: str = ""
    processing_time: float = 0.0


class BaseEngine(ABC):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = self.__class__.__name__

    @abstractmethod
    async def convert(self, pdf_path: str, **kwargs) -> OCRResult:
        ...

    @abstractmethod
    async def is_available(self) -> bool:
        ...

    @abstractmethod
    def get_metadata(self) -> dict:
        ...
