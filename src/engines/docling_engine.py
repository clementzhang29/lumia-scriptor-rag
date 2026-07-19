from .base import BaseEngine, OCRResult, extract_pdf_text_with_fitz
import time


class DoclingEngine(BaseEngine):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "Docling"

    async def convert(self, pdf_path: str, **kwargs) -> OCRResult:
        start = time.time()
        try:
            from docling.document_converter import DocumentConverter

            converter = DocumentConverter()
            result = converter.convert(pdf_path)
            markdown = result.document.export_to_markdown()
            return OCRResult(markdown=markdown, engine=self.name, processing_time=time.time() - start)
        except Exception as e:
            markdown = extract_pdf_text_with_fitz(pdf_path)
            if markdown:
                return OCRResult(
                    markdown=markdown,
                    metadata={"fallback": "fitz_text", "primary_error": str(e)},
                    engine=self.name,
                    processing_time=time.time() - start,
                )
            return OCRResult(success=False, error=str(e), engine=self.name, processing_time=time.time() - start)

    async def is_available(self) -> bool:
        try:
            import docling
            return True
        except Exception:
            return False

    def get_metadata(self) -> dict:
        return {"name": "Docling", "gpu": self.config.get("gpu", True), "lang": "multi"}
