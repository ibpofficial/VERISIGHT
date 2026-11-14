import logging
from typing import Dict, Optional, Type
from backend.app.engines.ocr.base import OCREngine, OCRResultDTO
from backend.app.engines.ocr.tesseract_engine import TesseractOCREngine
from backend.app.engines.ocr.paddle_engine import PaddleOCREngine
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class OCRRegistry:
    def __init__(self):
        self._engines: Dict[str, OCREngine] = {
            "tesseract": TesseractOCREngine(),
            "paddleocr": PaddleOCREngine(),
        }
        self.default_primary = getattr(settings, "OCR_PRIMARY_ENGINE", "paddleocr").lower()

    def get_engine(self, name: str) -> Optional[OCREngine]:
        return self._engines.get(name.lower())

    def extract_with_fallback(
        self,
        image_path: str,
        preferred_engine: Optional[str] = None
    ) -> OCRResultDTO:
        primary_name = (preferred_engine or self.default_primary).lower()
        if primary_name not in self._engines:
            primary_name = "tesseract"

        fallback_name = "tesseract" if primary_name == "paddleocr" else "paddleocr"

        primary_engine = self._engines[primary_name]
        fallback_engine = self._engines[fallback_name]

        # 1. Try Primary Engine
        try:
            res = primary_engine.extract(image_path)
            res.primary_engine = primary_name
            # If primary succeeded and was able to run (not ENGINE_UNAVAILABLE)
            if res.status == "SUCCESS":
                return res
            logger.warning(
                f"Primary OCR engine '{primary_name}' failed with status {res.status}: {res.error_message}. Falling back to '{fallback_name}'."
            )
        except Exception as e:
            logger.warning(f"Exception during primary OCR '{primary_name}': {str(e)}. Falling back to '{fallback_name}'.")

        # 2. Try Fallback Engine
        try:
            fallback_res = fallback_engine.extract(image_path)
            fallback_res.fallback_used = True
            fallback_res.primary_engine = primary_name
            return fallback_res
        except Exception as fb_err:
            return OCRResultDTO(
                engine_name=fallback_engine.engine_name,
                fields=[],
                raw_mrz_lines=[],
                full_text="",
                execution_time_ms=0,
                status="EXTRACTION_FAILED",
                error_message=f"Both primary ('{primary_name}') and fallback ('{fallback_name}') OCR engines failed: {str(fb_err)}",
                fallback_used=True,
                primary_engine=primary_name
            )


# Global singleton instance
ocr_registry = OCRRegistry()


def get_ocr_registry() -> OCRRegistry:
    return ocr_registry

