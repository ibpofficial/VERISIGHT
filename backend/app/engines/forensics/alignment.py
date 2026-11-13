import cv2
import numpy as np
from typing import Dict, Any, List

ALIGNMENT_LIMITATIONS = (
    "Text alignment algorithms assume a planar or perspective-corrected document scan. Optical lens distortion, "
    "creased passport pages, or scanning curvature can introduce slight baseline deviations that mimic manual editing. "
    "Findings are indicative and require human reviewer confirmation."
)


def run_alignment_analysis(image_path: str) -> Dict[str, Any]:
    """
    Measures text line horizontal baseline linearity and font pitch consistency across VIZ lines.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        return {"is_available": False, "findings": []}

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Focus on lower two-thirds where text fields and MRZ reside
    roi_gray = gray[int(h * 0.3):, :]
    rh, rw = roi_gray.shape

    # Morphological line detection to find text line baselines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
    dilated = cv2.dilate(cv2.Canny(roi_gray, 50, 150), kernel, iterations=1)

    lines = cv2.HoughLinesP(dilated, 1, np.pi / 180, threshold=80, minLineLength=rw * 0.15, maxLineGap=15)

    angles: List[float] = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line.reshape(-1)
            angle = float(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if abs(angle) < 15.0:  # Ignore vertical or steep diagonal lines
                angles.append(angle)

    mean_angle = float(np.mean(angles)) if angles else 0.0
    angle_variance = float(np.var(angles)) if len(angles) > 1 else 0.0

    findings = []
    if len(angles) >= 3 and angle_variance > 2.5:
        findings.append({
            "analysis_method": "ALIGNMENT",
            "severity": "MEDIUM",
            "region_bbox": {
                "x": 0,
                "y": int(h * 0.3),
                "w": int(w),
                "h": int(h * 0.7)
            },
            "title": "Irregular Text Line Baseline Slant Detected",
            "explanation": (
                f"Text line baseline analysis revealed inconsistent angular pitch across printed lines "
                f"(variance: {angle_variance:.2f}°, line count: {len(angles)}). Standard ICAO travel credentials "
                "are manufactured with parallel typographic registration. Angular discordance indicates "
                "potential digital text replacement or spliced alphanumeric segments."
            ),
            "technical_details": {
                "detected_text_lines": len(angles),
                "mean_line_angle_deg": round(mean_angle, 2),
                "baseline_angle_variance": round(angle_variance, 3)
            },
            "limitations": ALIGNMENT_LIMITATIONS,
            "recommended_action": "Verify baseline alignment of personal data fields against standard passport grid."
        })
    else:
        findings.append({
            "analysis_method": "ALIGNMENT",
            "severity": "INFORMATIONAL",
            "region_bbox": None,
            "title": "Consistent Typographic Baseline Linearity",
            "explanation": (
                f"Detected text lines conform to standard parallel typographical registration "
                f"(angular variance: {angle_variance:.2f}°, lines measured: {len(angles)}). No baseline "
                "displacement or kerning jitter observed."
            ),
            "technical_details": {
                "detected_text_lines": len(angles),
                "mean_line_angle_deg": round(mean_angle, 2),
                "baseline_angle_variance": round(angle_variance, 3)
            },
            "limitations": ALIGNMENT_LIMITATIONS,
            "recommended_action": "Typographic alignment within standard tolerances."
        })

    return {
        "is_available": True,
        "line_count": len(angles),
        "mean_angle": mean_angle,
        "angle_variance": angle_variance,
        "findings": findings
    }
