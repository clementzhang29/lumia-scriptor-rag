from .base import BaseEngine, OCRResult, extract_pdf_text_with_fitz
import time


class PaddleOCREngine(BaseEngine):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "PaddleOCR"

    async def convert(self, pdf_path: str, **kwargs) -> OCRResult:
        start = time.time()
        try:
            from paddleocr import PaddleOCR

            ocr = PaddleOCR(lang=self.config.get("lang", "ch"))
            predictions = ocr.predict(pdf_path)

            full_text: list[str] = []
            for page in predictions or []:
                page_text = page.get("rec_texts") or []
                if page_text:
                    full_text.append("\n".join(page_text))

            return OCRResult(
                markdown="\n\n".join(full_text),
                engine=self.name,
                processing_time=time.time() - start,
            )
        except Exception as e:
            markdown = extract_pdf_text_with_fitz(pdf_path)
            if markdown:
                return OCRResult(
                    markdown=markdown,
                    engine=self.name,
                    processing_time=time.time() - start,
                    metadata={"fallback": "fitz_text", "primary_error": str(e)},
                )
            return OCRResult(success=False, error=str(e), engine=self.name, processing_time=time.time() - start)

    async def is_available(self) -> bool:
        try:
            import paddleocr
            return True
        except Exception:
            return False

    def get_metadata(self) -> dict:
        return {"name": "PaddleOCR", "gpu": self.config.get("gpu", True), "lang": self.config.get("lang", "ch")}
