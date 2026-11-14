import os
import re
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.engines.ocr.tesseract_engine import TesseractOCREngine
from backend.app.engines.ocr.field_validator import compute_field_validation_status
from backend.app.models import ValidationStatus

client = TestClient(app)

FORBIDDEN_PATTERNS = [
    r'\bSHARMA\b',
    r'\bAMIT\b',
    r'\bUTOPIA\b',
    r'14/05/1988',
    r'\bA12345678\b',
]


def test_no_fabricated_strings_in_production_code():
    """CI Guard: Fails if fabricated identity strings appear in non-test source code."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    app_dir = os.path.join(repo_root, "backend", "app")
    frontend_dir = os.path.join(repo_root, "frontend", "src")

    hits = []
    # Scan backend production code
    for root, _, files in os.walk(app_dir):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, 1):
                        for pattern in FORBIDDEN_PATTERNS:
                            if re.search(pattern, line):
                                hits.append(f"{path}:{line_idx} - Pattern {pattern} found in: {line.strip()}")

    # Scan frontend production code
    if os.path.exists(frontend_dir):
        for root, _, files in os.walk(frontend_dir):
            for file in files:
                if file.endswith((".ts", ".tsx")):
                    path = os.path.join(root, file)
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_idx, line in enumerate(f, 1):
                            for pattern in FORBIDDEN_PATTERNS:
                                if re.search(pattern, line):
                                    hits.append(f"{path}:{line_idx} - Pattern {pattern} found in: {line.strip()}")

    assert len(hits) == 0, f"Fabricated test strings detected in production source code:\n" + "\n".join(hits)


def test_health_live_and_ready_endpoints():
    """Verifies that /health/live and /health/ready execute genuine health probes."""
    # 1. Liveness
    live_res = client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "ALIVE"

    # 2. Readiness
    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 200
    ready_data = ready_res.json()
    assert ready_data["status"] == "READY"
    assert ready_data["database"] == "CONNECTED"
    assert ready_data["storage"] == "WRITABLE"
    assert "ocr_engines" in ready_data

    # 3. Legacy compatibility
    legacy_res = client.get("/health")
    assert legacy_res.status_code == 200
    assert legacy_res.json()["status"] == "HEALTHY"


def test_degenerate_inputs_produce_no_identity_fields():
    """
    Asserts that blank images, random non-document photos, and text-only code pages
    produce ZERO identity fields with values (all missing / null).
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    fixtures_dir = os.path.join(repo_root, "tests", "fixtures")

    blank_path = os.path.join(fixtures_dir, "sample_25_blank_white.png")
    photo_path = os.path.join(fixtures_dir, "sample_23_random_photo_nature.jpg")
    code_path = os.path.join(fixtures_dir, "sample_28_text_only_code.png")

    ocr_engine = TesseractOCREngine()

    for path in (blank_path, photo_path, code_path):
        if not os.path.exists(path):
            continue
        res = ocr_engine.extract(path)
        # Check that no identity credential fields were populated with fake values
        extracted_values = [f.value for f in res.fields if f.value is not None]
        assert len(extracted_values) == 0, f"Expected 0 identity fields for {os.path.basename(path)}, got: {extracted_values}"
        # All reported fields should be MISSING
        for field in res.fields:
            assert field.validation_status == "MISSING" or field.value is None


def test_field_validation_status_logic():
    """Verifies format checks and confidence thresholds without hardcoded defaults."""
    # Missing / empty
    assert compute_field_validation_status("surname", None, None) == ValidationStatus.MISSING
    assert compute_field_validation_status("surname", "", 0.9) == ValidationStatus.MISSING

    # Low confidence floor
    assert compute_field_validation_status("surname", "KUMAR", 0.35) == ValidationStatus.LOW_CONFIDENCE

    # Invalid dates
    assert compute_field_validation_status("date_of_birth", "32/13/2020", 0.9) == ValidationStatus.INVALID_FORMAT
    assert compute_field_validation_status("date_of_birth", "NOT_A_DATE", 0.9) == ValidationStatus.INVALID_FORMAT

    # Invalid Document Number
    assert compute_field_validation_status("document_number", "DOC!#$", 0.9) == ValidationStatus.INVALID_FORMAT

    # Valid values
    assert compute_field_validation_status("date_of_birth", "14/05/1990", 0.95) == ValidationStatus.VALID
    assert compute_field_validation_status("document_number", "A2098411", 0.95) == ValidationStatus.VALID
    assert compute_field_validation_status("sex", "M", 0.95) == ValidationStatus.VALID

