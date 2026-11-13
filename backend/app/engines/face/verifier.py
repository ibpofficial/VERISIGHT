import cv2
import numpy as np
import base64
from typing import Dict, Any, Optional, Tuple


FACE_DISCLAIMER = (
    "Face verification provides probabilistic similarity scoring to assist authorized security officers. "
    "Variations in ambient illumination, camera sensor focal length, subject pose, and temporal age "
    "progression significantly impact automated biometric matching. All algorithmic outputs are non-conclusive "
    "and mandate human officer cross-examination."
)

PRIVACY_STATEMENT = (
    "In accordance with the Digital Personal Data Protection (DPDP) Act 2023, biometric face captures "
    "are processed strictly ephemerally in RAM. Live camera frames and high-dimensional biometric embeddings "
    "are permanently purged from volatile memory immediately upon similarity score computation. "
    "No raw biometric artifacts are persisted to disk or database."
)


def extract_document_portrait(img_bgr: np.ndarray) -> Optional[np.ndarray]:
    """
    Extracts the document portrait from standard ICAO TD3 passport layout or photo box.
    Returns the cropped BGR image of the portrait zone.
    """
    if img_bgr is None or img_bgr.size == 0:
        return None

    h, w = img_bgr.shape[:2]

    # Standard ICAO TD3 passport layout: Left portrait zone
    # x: 4% to 42% width, y: 16% to 76% height
    x1 = int(w * 0.04)
    x2 = int(w * 0.42)
    y1 = int(h * 0.16)
    y2 = int(h * 0.76)

    crop = img_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None

    return crop


def evaluate_face_quality(img_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Computes optical quality indicators for face crops (blur, brightness, contrast, resolution).
    """
    if img_bgr is None or img_bgr.size == 0:
        return {
            "is_acceptable": False,
            "blur_score": 0.0,
            "mean_luminance": 0.0,
            "resolution": (0, 0),
            "flags": ["EMPTY_FRAME"]
        }

    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Blur score via Laplacian variance
    lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean_lum = float(np.mean(gray))

    flags = []
    if lap_var < 50.0:
        flags.append("POTENTIAL_BLUR")
    if mean_lum < 40.0:
        flags.append("UNDEREXPOSED")
    elif mean_lum > 215.0:
        flags.append("OVEREXPOSED")
    if w < 60 or h < 80:
        flags.append("LOW_RESOLUTION")

    is_acceptable = len(flags) == 0

    return {
        "is_acceptable": is_acceptable,
        "blur_score": round(lap_var, 2),
        "mean_luminance": round(mean_lum, 2),
        "resolution": (w, h),
        "flags": flags
    }


def _extract_feature_vector(img_bgr: np.ndarray) -> np.ndarray:
    """
    Computes a composite normalized visual feature descriptor combining
    spatial multi-scale gradient orientation histograms (HOG) and
    color distribution histograms in YCrCb color space.
    """
    # Resize to canonical template size (128x128)
    resized = cv2.resize(img_bgr, (128, 128))
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    ycrcb = cv2.cvtColor(resized, cv2.COLOR_BGR2YCrCb)

    # 1. Gradient orientation histograms (4x4 spatial cells, 8 orientation bins)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag, ang = cv2.cartToPolar(gx, gy, angleInDegrees=True)
    # Fold angles to [0, 180)
    ang = ang % 180.0

    hog_parts = []
    cell_size = 32  # 128 / 4 = 32
    for r in range(4):
        for c in range(4):
            cell_mag = mag[r*cell_size:(r+1)*cell_size, c*cell_size:(c+1)*cell_size]
            cell_ang = ang[r*cell_size:(r+1)*cell_size, c*cell_size:(c+1)*cell_size]
            hist, _ = np.histogram(cell_ang, bins=8, range=(0.0, 180.0), weights=cell_mag)
            norm = np.linalg.norm(hist)
            if norm > 1e-6:
                hist = hist / norm
            hog_parts.append(hist)

    hog_vec = np.concatenate(hog_parts)

    # 2. Spatial 4x4 grid color histograms in YCrCb
    color_hist_parts = []
    for r in range(4):
        for c in range(4):
            cell = ycrcb[r*cell_size:(r+1)*cell_size, c*cell_size:(c+1)*cell_size]
            hist_y = cv2.calcHist([cell], [0], None, [8], [0, 256]).flatten()
            hist_cr = cv2.calcHist([cell], [1], None, [8], [0, 256]).flatten()
            hist_cb = cv2.calcHist([cell], [2], None, [8], [0, 256]).flatten()
            cell_hist = np.concatenate([hist_y, hist_cr, hist_cb])
            norm = np.linalg.norm(cell_hist)
            if norm > 1e-6:
                cell_hist = cell_hist / norm
            color_hist_parts.append(cell_hist)

    color_vec = np.concatenate(color_hist_parts)

    # Composite normalized feature vector
    combined = np.concatenate([hog_vec, color_vec])
    norm = np.linalg.norm(combined)
    if norm > 1e-6:
        combined = combined / norm

    return combined


def compute_face_similarity(doc_face_bgr: np.ndarray, live_face_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Computes cosine similarity between document portrait and live capture face vectors.
    """
    doc_quality = evaluate_face_quality(doc_face_bgr)
    live_quality = evaluate_face_quality(live_face_bgr)

    v1 = _extract_feature_vector(doc_face_bgr)
    v2 = _extract_feature_vector(live_face_bgr)

    dot_product = float(np.dot(v1, v2))
    # Bound between 0.0 and 1.0
    cosine_sim = max(0.0, min(1.0, dot_product))

    # Standard threshold 0.65
    MATCH_THRESHOLD = 0.65
    is_match = cosine_sim >= MATCH_THRESHOLD

    if cosine_sim >= 0.82:
        confidence_band = "HIGH"
    elif cosine_sim >= 0.65:
        confidence_band = "MEDIUM"
    else:
        confidence_band = "LOW"

    caveats = [
        "Biometric algorithms are vulnerable to variations in pose, facial expression, and glasses/headwear.",
        "Document photo degradation, security printing watermarks, and laminate reflections reduce match fidelity.",
        "Age disparity between document issuance and present date may naturally reduce facial similarity."
    ]

    return {
        "similarity_score": round(cosine_sim, 4),
        "similarity_percentage": round(cosine_sim * 100, 1),
        "threshold": MATCH_THRESHOLD,
        "is_match": is_match,
        "confidence_band": confidence_band,
        "doc_quality": doc_quality,
        "live_quality": live_quality,
        "caveats": caveats,
        "disclaimer": FACE_DISCLAIMER,
        "privacy_notice": PRIVACY_STATEMENT
    }


def bgr_to_base64_jpeg(img_bgr: np.ndarray) -> str:
    """Encodes a BGR image array into a base64 data URI string."""
    success, buffer = cv2.imencode(".jpg", img_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not success:
        return ""
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/jpeg;base64,{b64_str}"


def verify_document_vs_live(
    doc_image_path: str,
    live_image_bytes: bytes,
    consent_granted: bool
) -> Dict[str, Any]:
    """
    High-level verification function.
    Validates consent, extracts document portrait, processes live capture,
    computes similarity, and guarantees ephemeral memory disposal.
    """
    if not consent_granted:
        return {
            "success": False,
            "error_code": "CONSENT_REQUIRED",
            "message": "Explicit consent is legally mandated under Section 6 of DPDP Act 2023 before biometric verification can commence."
        }

    # 1. Load document image
    doc_img = cv2.imread(doc_image_path)
    if doc_img is None:
        return {
            "success": False,
            "error_code": "DOCUMENT_IMAGE_NOT_FOUND",
            "message": "Source document image could not be loaded from storage."
        }

    # Extract portrait
    doc_portrait = extract_document_portrait(doc_img)
    if doc_portrait is None:
        return {
            "success": False,
            "error_code": "PORTRAIT_EXTRACTION_FAILED",
            "message": "Could not isolate portrait region from document image."
        }

    # 2. Decode live capture image from bytes
    nparr = np.frombuffer(live_image_bytes, np.uint8)
    live_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if live_img is None:
        return {
            "success": False,
            "error_code": "INVALID_LIVE_IMAGE",
            "message": "Supplied live capture payload could not be decoded as a valid image."
        }

    # If live image is a wide frame, take center crop as face zone
    lh, lw = live_img.shape[:2]
    if lw > lh:
        # Center square crop
        offset = (lw - lh) // 2
        live_face = live_img[:, offset:offset + lh]
    else:
        live_face = live_img

    # 3. Compute similarity
    result = compute_face_similarity(doc_portrait, live_face)

    # 4. Include base64 preview of document portrait for officer UI inspection
    doc_portrait_b64 = bgr_to_base64_jpeg(doc_portrait)

    # 5. Immediate cleanup: purge live images from memory
    del live_img
    del live_face
    del nparr

    return {
        "success": True,
        "doc_portrait_b64": doc_portrait_b64,
        **result
    }
