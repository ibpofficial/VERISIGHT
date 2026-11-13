import os
import io
import pytest
import numpy as np
import cv2
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.engines.forensics.ela import run_error_level_analysis
from backend.app.engines.forensics.metadata import run_metadata_inspection
from backend.app.engines.forensics.texture import run_texture_analysis
from backend.app.engines.forensics.alignment import run_alignment_analysis
from backend.app.engines.forensics.portrait import run_portrait_analysis

client = TestClient(app)


@pytest.fixture
def test_images(tmp_path):
    # 1. Clean synthetic image
    clean_path = str(tmp_path / "clean_doc.jpg")
    img = np.full((400, 600, 3), 240, dtype=np.uint8)
    # Add some text lines
    cv2.putText(img, "REPUBLIC OF INDIA / PASSPORT", (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(img, "P<INDKUMAR<<ANIL<<<<<<<<<<<<<<<<<<<<<<<<<<<<", (50, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10, 10, 10), 1)
    cv2.putText(img, "Z1234567<4IND9001015M3001018<<<<<<<<<<<<<<02", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (10, 10, 10), 1)
    cv2.imwrite(clean_path, img)

    # 2. Tampered image with foreign spliced square
    tampered_path = str(tmp_path / "tampered_doc.jpg")
    t_img = img.copy()
    # Add a high-contrast noise block simulating an edited photo
    noise_block = np.random.randint(0, 255, (120, 120, 3), dtype=np.uint8)
    t_img[100:220, 60:180] = noise_block
    cv2.imwrite(tampered_path, t_img)

    heatmap_path = str(tmp_path / "ela_heatmap.jpg")

    return {
        "clean": clean_path,
        "tampered": tampered_path,
        "heatmap": heatmap_path
    }


def test_error_level_analysis_clean_and_tampered(test_images):
    # Test clean image
    clean_res = run_error_level_analysis(test_images["clean"], test_images["heatmap"])
    assert clean_res["is_available"] is True
    assert os.path.exists(test_images["heatmap"])
    assert len(clean_res["findings"]) > 0

    # Test tampered image
    tampered_res = run_error_level_analysis(test_images["tampered"], test_images["heatmap"])
    assert tampered_res["is_available"] is True
    # The random noise block will trigger an anomaly
    assert tampered_res["max_error"] > clean_res["mean_error"]


def test_metadata_inspection(test_images):
    res = run_metadata_inspection(test_images["clean"])
    assert res["is_available"] is True
    assert len(res["findings"]) > 0
    # Clean OpenCV image won't have Photoshop metadata
    assert len(res["software_detected"]) == 0


def test_texture_analysis(test_images):
    res = run_texture_analysis(test_images["clean"])
    assert res["is_available"] is True
    assert "mean_variance" in res
    assert len(res["findings"]) > 0


def test_alignment_analysis(test_images):
    res = run_alignment_analysis(test_images["clean"])
    assert res["is_available"] is True
    assert "mean_angle" in res
    assert len(res["findings"]) > 0


def test_portrait_analysis(test_images):
    res = run_portrait_analysis(test_images["clean"])
    assert res["is_available"] is True
    assert "portrait_bbox" in res
    assert len(res["findings"]) > 0


def test_forensics_api_endpoints(test_images):
    # 1. Login to get token
    login_res = client.post("/api/v1/auth/login", json={
        "email": "officer@verisight.gov.in",
        "password": "Officer@12345"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload document to create a screening
    with open(test_images["tampered"], "rb") as f:
        upload_res = client.post(
            "/api/v1/screenings",
            headers=headers,
            data={"document_type": "PASSPORT_TD3", "issuing_country_code": "IND", "is_synthetic": True},
            files={"file": ("passport.jpg", f, "image/jpeg")}
        )
    assert upload_res.status_code == 200
    screening_id = upload_res.json()["id"]

    # 3. Call GET /api/v1/forensics/{screening_id}
    forensics_res = client.get(f"/api/v1/forensics/{screening_id}", headers=headers)
    assert forensics_res.status_code == 200
    findings = forensics_res.json()
    assert len(findings) >= 4  # Should include ELA, Metadata, Texture, Alignment, Portrait

    # 4. Call GET /api/v1/forensics/{screening_id}/heatmap
    heatmap_res = client.get(f"/api/v1/forensics/{screening_id}/heatmap", headers=headers)
    assert heatmap_res.status_code == 200
    assert heatmap_res.headers["content-type"] == "image/jpeg"
