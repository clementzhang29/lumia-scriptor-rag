from .base import BaseEngine, OCRResult, extract_pdf_text_with_fitz
import time


class NougatEngine(BaseEngine):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "Nougat"

    async def convert(self, pdf_path: str, **kwargs) -> OCRResult:
        start = time.time()
        try:
            from nougat import NougatModel
            from nougat.utils.dataset import PDFDataset

            model = NougatModel.from_pretrained("facebook/nougat-base")
            dataset = PDFDataset(pdf_path)
            texts = []
            for page in dataset:
                output = model.inference(page)
                texts.append(output)
            return OCRResult(markdown="\n\n".join(texts), engine=self.name, processing_time=time.time() - start)
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
            import nougat
            return True
        except Exception:
            return False

    def get_metadata(self) -> dict:
        return {"name": "Nougat", "gpu": self.config.get("gpu", True), "lang": "en"}
