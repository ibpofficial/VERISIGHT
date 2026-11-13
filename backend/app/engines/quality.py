import cv2
import numpy as np
from typing import Dict, Any, List


def assess_image_quality(image_path: str) -> Dict[str, Any]:
    """
    Evaluates optical and geometric quality of an ingested identity document image:
    1. Blur: Modified Laplacian variance (threshold < 100 flags blur)
    2. Glare: Proportion of saturated pixels (luminance >= 250)
    3. Brightness: Mean grayscale luminance (optimal range: 90 - 200)
    4. Resolution DPI: Estimated DPI assuming standard passport (ID-3: 125x88mm)
    5. Orientation: Rough angle check based on aspect ratio
    6. Readability score: Weighted combination (0.0 to 1.0)
    7. Rescan recommendation: Flagged if severe blur or glare degrades reliability
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Unable to read image at {image_path}")

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Blur via Laplacian variance
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    blur_score = min(laplacian_var, 500.0)  # normalized cap

    # 2. Glare (Overexposure)
    saturated_pixels = np.sum(gray >= 250)
    total_pixels = h * w
    glare_ratio = float(saturated_pixels / total_pixels)

    # 3. Brightness
    mean_brightness = float(np.mean(gray))

    # 4. Estimated DPI (Standard ID-3 passport is ~4.92 x 3.46 inches)
    estimated_dpi = int(max(w / 4.92, h / 3.46))

    # 5. Orientation (Passport TD3 is landscape ~1.42 aspect ratio)
    aspect_ratio = w / h if h > 0 else 1.0
    orientation = 0
    if aspect_ratio < 0.9:
        orientation = 90  # portrait orientation, needs rotation

    # 6. Border crop detection (check if borders are tightly clipped)
    is_cropped = False
    edge_strip_top = gray[0:5, :]
    edge_strip_bottom = gray[h-5:h, :]
    if np.std(edge_strip_top) > 40 or np.std(edge_strip_bottom) > 40:
        is_cropped = True

    # 7. Collect issues detected
    issues: List[str] = []
    if blur_score < 100.0:
        issues.append("OPTICAL_BLUR_DETECTED: Laplacian variance below threshold (score < 100)")
    if glare_ratio > 0.04:
        issues.append(f"SURFACE_GLARE_DETECTED: {glare_ratio*100:.1f}% pixels overexposed")
    if mean_brightness < 70.0:
        issues.append("UNDEREXPOSURE_DETECTED: Insufficient ambient lighting")
    elif mean_brightness > 220.0:
        issues.append("OVEREXPOSURE_DETECTED: Overall brightness exceeds optimal range")
    if estimated_dpi < 200:
        issues.append(f"LOW_RESOLUTION_DETECTED: Estimated {estimated_dpi} DPI (minimum 300 recommended)")
    if orientation != 0:
        issues.append("ORIENTATION_MISMATCH: Document image rotated 90 degrees")

    # 8. Compute normalized readability score (0.0 to 1.0)
    blur_norm = min(blur_score / 250.0, 1.0)
    glare_penalty = max(0.0, 1.0 - (glare_ratio * 15.0))
    brightness_norm = 1.0 - (abs(mean_brightness - 140.0) / 140.0)
    brightness_norm = max(0.0, min(1.0, brightness_norm))

    readability = float(0.45 * blur_norm + 0.35 * glare_penalty + 0.20 * brightness_norm)
    readability = round(max(0.05, min(0.99, readability)), 2)

    # 9. Rescan recommendation & Acceptability
    rescan_recommended = (blur_score < 80.0) or (glare_ratio > 0.06) or (estimated_dpi < 150)
    is_acceptable = not rescan_recommended

    return {
        "overall_score": readability,
        "is_acceptable": is_acceptable,
        "blur_score": round(blur_score, 1),
        "brightness_score": round(mean_brightness, 1),
        "glare_score": round(glare_ratio, 4),
        "resolution_dpi": estimated_dpi,
        "orientation_detected": orientation,
        "is_cropped": is_cropped,
        "readability_score": readability,
        "issues_detected": issues,
        "rescan_recommended": rescan_recommended,
    }
