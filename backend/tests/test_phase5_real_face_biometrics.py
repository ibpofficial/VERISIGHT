import pytest
import numpy as np
import cv2

from backend.app.engines.face.verifier import (
    detect_face_in_image,
    extract_document_portrait,
    evaluate_face_quality,
    compute_face_similarity,
    verify_document_vs_live
)


def create_sample_face_bgr(w=160, h=180):
    img = np.full((h, w, 3), (180, 160, 140), dtype=np.uint8)
    # Eyes
    cv2.circle(img, (w // 3, h // 3), 10, (50, 40, 30), -1)
    cv2.circle(img, (2 * w // 3, h // 3), 10, (50, 40, 30), -1)
    # Nose & Mouth
    cv2.line(img, (w // 2, h // 3 + 10), (w // 2, h // 2 + 10), (70, 50, 40), 2)
    cv2.ellipse(img, (w // 2, 2 * h // 3), (30, 12), 0, 0, 180, (40, 30, 80), 3)
    return img


def test_face_detection_and_bounding_box():
    face = create_sample_face_bgr()
    detected = detect_face_in_image(face)
    assert detected is not None
    crop, bbox = detected
    assert "x" in bbox and "y" in bbox and "w" in bbox and "h" in bbox
    assert bbox["w"] >= 50
    assert bbox["h"] >= 50


def test_no_face_detected_on_blank_image():
    blank = np.zeros((300, 300, 3), dtype=np.uint8)
    detected = detect_face_in_image(blank)
    assert detected is None


def test_quality_rejection_on_small_or_blurry_faces():
    # Tiny face < 60x60
    tiny_face = create_sample_face_bgr(40, 40)
    tiny_quality = evaluate_face_quality(tiny_face)
    assert "LOW_RESOLUTION_FACE_TOO_SMALL" in tiny_quality["flags"]
    assert tiny_quality["is_acceptable"] is False

    # Blurry face
    normal_face = create_sample_face_bgr(200, 200)
    blurred_face = cv2.GaussianBlur(normal_face, (31, 31), 0)
    blur_quality = evaluate_face_quality(blurred_face)
    assert "POTENTIAL_BLUR" in blur_quality["flags"]
    assert blur_quality["blur_score"] < 45.0


def test_calibrated_cosine_similarity_and_verdicts():
    f1 = create_sample_face_bgr(160, 180)
    f2 = create_sample_face_bgr(160, 180)

    res = compute_face_similarity(f1, f2)
    assert -1.0 <= res["cosine_similarity"] <= 1.0
    assert res["threshold"] == 0.40
    assert res["is_match"] is True
    assert res["match_verdict"] == "MATCH"
    assert res["confidence_band"] == "HIGH"

    # Completely different image (white noise)
    noise = np.random.randint(0, 255, (160, 180, 3), dtype=np.uint8)
    noise_res = compute_face_similarity(f1, noise)
    assert noise_res["match_verdict"] in ("NO_MATCH", "INCONCLUSIVE")


def test_dpdp_consent_and_ephemeral_processing(tmp_path):
    face_img = create_sample_face_bgr()
    doc_path = str(tmp_path / "doc_face.jpg")
    cv2.imwrite(doc_path, face_img)

    _, buf = cv2.imencode(".jpg", face_img)
    live_bytes = buf.tobytes()

    # Consent False
    res_rejected = verify_document_vs_live(doc_path, live_bytes, consent_granted=False)
    assert res_rejected["success"] is False
    assert res_rejected["error_code"] == "CONSENT_REQUIRED"
    assert "DPDP Act 2023" in res_rejected["message"]

    # Consent True
    res_allowed = verify_document_vs_live(doc_path, live_bytes, consent_granted=True)
    assert res_allowed["success"] is True
    assert res_allowed["is_match"] is True
    assert "doc_portrait_b64" in res_allowed
    assert "live_face_bbox" in res_allowed
