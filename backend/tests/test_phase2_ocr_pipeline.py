import os
import cv2
import numpy as np
import pytest
from datetime import datetime

from backend.app.engines.ocr.registry import OCRRegistry, get_ocr_registry
from backend.app.engines.ocr.paddle_engine import PaddleOCREngine
from backend.app.engines.ocr.tesseract_engine import TesseractOCREngine
from backend.app.engines.ocr.field_validator import parse_date_with_century_inference
from backend.app.engines.preprocessing import correct_perspective_contour, preprocess_document_image


def test_ocr_registry_initialization():
    registry = get_ocr_registry()
    assert registry.get_engine("tesseract") is not None
    assert registry.get_engine("paddleocr") is not None
    assert isinstance(registry.get_engine("tesseract"), TesseractOCREngine)
    assert isinstance(registry.get_engine("paddleocr"), PaddleOCREngine)


def test_ocr_registry_fallback_behavior(tmp_path):
    registry = OCRRegistry()
    # Create empty test image
    img_path = str(tmp_path / "test_reg.png")
    cv2.imwrite(img_path, np.full((100, 100, 3), 255, dtype=np.uint8))

    # Request paddleocr as primary; since paddleocr package is not installed on host,
    # it should trigger fallback to tesseract and record fallback_used=True
    res = registry.extract_with_fallback(img_path, preferred_engine="paddleocr")
    assert res.fallback_used is True
    assert res.primary_engine == "paddleocr"
    assert res.engine_name == "Tesseract-OCR"


def test_date_parsing_and_century_inference():
    # 4-digit full calendar date
    dt, method = parse_date_with_century_inference("15/08/1990", is_expiry=False)
    assert dt == datetime(1990, 8, 15)
    assert method == "EXPLICIT_4_DIGIT_YEAR"

    dt, method = parse_date_with_century_inference("20/12/2032", is_expiry=True)
    assert dt == datetime(2032, 12, 20)
    assert method == "EXPLICIT_4_DIGIT_YEAR"

    # 6-digit ICAO MRZ Date: DOB (past century: 900815 -> 1990)
    dt_dob, m_dob = parse_date_with_century_inference("900815", is_expiry=False)
    assert dt_dob == datetime(1990, 8, 15)
    assert m_dob == "EXPLICIT_DOB_20TH_CENTURY_INFERENCE"

    # 6-digit ICAO MRZ Date: Expiry (21st century: 321220 -> 2032)
    dt_exp, m_exp = parse_date_with_century_inference("321220", is_expiry=True)
    assert dt_exp == datetime(2032, 12, 20)
    assert m_exp == "EXPLICIT_EXPIRY_21ST_CENTURY_INFERENCE"

    # Invalid dates
    dt_inv, m_inv = parse_date_with_century_inference("999999", is_expiry=False)
    assert dt_inv is None
    assert "INVALID" in m_inv


def test_perspective_rectification_on_trapezoid():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    trap_path = os.path.join(repo_root, "tests", "fixtures", "sample_11_perspective_trapezoid.jpg")
    if os.path.exists(trap_path):
        img = cv2.imread(trap_path)
        warped, applied = correct_perspective_contour(img)
        assert warped is not None
        assert warped.shape[0] > 0

