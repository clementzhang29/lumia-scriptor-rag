"""MinerU 引擎封装 — magic-pdf 1.x 兼容。"""
from .base import BaseEngine, OCRResult, extract_pdf_text_with_fitz
import json
import os
import shutil
import tempfile
import time
from pathlib import Path


def _ensure_cpu_env() -> None:
    os.environ["CUDA_VISIBLE_DEVICES"] = ""


def _ensure_mineru_config() -> Path:
    data_root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ZCLUM Prism OCR"
    config_path = data_root / "magic-pdf.json"
    os.environ.setdefault("MINERU_TOOLS_CONFIG_JSON", str(config_path))
    if config_path.exists():
        return config_path
    config_path.parent.mkdir(parents=True, exist_ok=True)
    models_dir = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "datalab" / "datalab" / "Cache" / "models"
    config_path.write_text(
        json.dumps({"models-dir": str(models_dir), "device-mode": "cpu"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return config_path


class MinerUEngine(BaseEngine):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.name = "MinerU"

    async def convert(self, pdf_path: str, **kwargs) -> OCRResult:
        start = time.time()
        _ensure_cpu_env()
        _ensure_mineru_config()
        try:
            from magic_pdf.tools.common import do_parse
            from magic_pdf.config.enums import SupportedPdfParseMethod
            from magic_pdf.config.make_content_config import MakeMode
            from magic_pdf.data.data_reader_writer import FileBasedDataWriter
            from magic_pdf.data.dataset import PymuDocDataset
            import fitz

            output_dir = Path(tempfile.mkdtemp(prefix="mineru_"))
            pdf_stem = Path(pdf_path).stem
            local_md_dir = output_dir / pdf_stem / "ocr"
            local_md_dir.mkdir(parents=True, exist_ok=True)

            FileBasedDataWriter(str(local_md_dir))
            ds = PymuDocDataset(fitz.open(pdf_path).tobytes(), lang=kwargs.get("lang", None))

            do_parse(
                output_dir=str(output_dir),
                pdf_file_name=pdf_stem,
                pdf_bytes_or_dataset=ds,
                model_list=[],
                parse_method=SupportedPdfParseMethod.OCR,
                debug_able=False,
                f_draw_span_bbox=False,
                f_draw_layout_bbox=False,
                f_dump_md=True,
                f_dump_middle_json=False,
                f_dump_model_json=False,
                f_dump_orig_pdf=False,
                f_dump_content_list=False,
                f_make_md_mode=MakeMode.MM_MD,
                lang=kwargs.get("lang", None),
            )

            md_path = local_md_dir / f"{pdf_stem}.md"
            markdown = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
            shutil.rmtree(output_dir, ignore_errors=True)
            if markdown:
                return OCRResult(markdown=markdown, engine=self.name, processing_time=time.time() - start)
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

        markdown = extract_pdf_text_with_fitz(pdf_path)
        if markdown:
            return OCRResult(
                markdown=markdown,
                engine=self.name,
                processing_time=time.time() - start,
                metadata={"fallback": "fitz_text", "primary_error": "mineru returned empty markdown"},
            )
        return OCRResult(success=False, error="MinerU returned empty markdown", engine=self.name, processing_time=time.time() - start)

    async def is_available(self) -> bool:
        try:
            import magic_pdf  # noqa: F401
            return True
        except Exception:
            return False

    def get_metadata(self) -> dict:
        return {
            "name": "MinerU",
            "gpu": self.config.get("gpu", True),
            "lang": "multi",
        }
