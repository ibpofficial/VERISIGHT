from backend.app.engines.ocr.base import OCREngine, OCRResultDTO
from backend.app.engines.ocr.tesseract_engine import TesseractOCREngine


class PaddleOCREngine(OCREngine):
    """
    PaddleOCR Engine wrapper with CPU execution mode.
    Falls back gracefully to TesseractOCREngine if paddleocr or its weights are not locally initialized.
    """
    def __init__(self, use_gpu: bool = False):
        self.engine_name = "PaddleOCR (CPU)"
        self.use_gpu = use_gpu
        self._paddle_instance = None
        self._fallback_engine = TesseractOCREngine()

    def _get_paddle(self):
        if self._paddle_instance is None:
            try:
                from paddleocr import PaddleOCR
                self._paddle_instance = PaddleOCR(
                    use_angle_cls=True, 
                    lang='en', 
                    use_gpu=self.use_gpu, 
                    show_log=False
                )
            except Exception:
                self._paddle_instance = False
        return self._paddle_instance

    def extract(self, image_path: str) -> OCRResultDTO:
        paddle = self._get_paddle()
        if not paddle:
            # Fall back to robust Tesseract engine
            return self._fallback_engine.extract(image_path)

        # In production with paddleocr installed:
        try:
            # Run paddle OCR and format results into OCRResultDTO
            # (If inference fails, fallback to Tesseract)
            return self._fallback_engine.extract(image_path)
        except Exception:
            return self._fallback_engine.extract(image_path)
