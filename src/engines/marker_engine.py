from .base import BaseEngine, OCRResult, extract_pdf_text_with_fitz
import time


class MarkerEngine(BaseEngine):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "Marker"

    async def convert(self, pdf_path: str, **kwargs) -> OCRResult:
        start = time.time()
        try:
            from marker.converters.pdf import PdfConverter
            from marker.models import create_model_dict
            from marker.output import text_from_rendered

            converter = PdfConverter(artifact_dict=create_model_dict())
            rendered = converter(pdf_path)
            markdown, _, images = text_from_rendered(rendered)
            metadata = getattr(rendered, "metadata", {}) or {}
            if images:
                metadata["images"] = list(images.keys())
            return OCRResult(markdown=markdown, metadata=metadata, engine=self.name, processing_time=time.time() - start)
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
            import marker
            return True
        except Exception:
            return False

    def get_metadata(self) -> dict:
        return {"name": "Marker", "gpu": self.config.get("gpu", True), "lang": "multi"}
