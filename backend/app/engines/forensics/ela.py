import os
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from PIL import Image
import io

ELA_LIMITATIONS = (
    "Error Level Analysis (ELA) highlights differences in compression error rates across 8x8 DCT blocks. "
    "High variance can occur naturally from high-contrast physical edges, printed security guilloche patterns, "
    "or camera focus. ELA is an evidentiary clue and NOT definitive proof of forgery."
)


def run_error_level_analysis(
    image_path: str,
    output_heatmap_path: str,
    quality: int = 95,
    scale_multiplier: float = 12.0
) -> Dict[str, Any]:
    """
    Executes Error Level Analysis on the document image.
    Re-saves at quality 95, computes absolute difference, generates a JET colormap heatmap,
    and inspects for localized anomalous error variance.
    """
    orig_bgr = cv2.imread(image_path)
    if orig_bgr is None:
        return {
            "is_available": False,
            "findings": []
        }

    h, w, c = orig_bgr.shape

    # 1. Recompress in memory at specified JPEG quality
    is_success, buffer = cv2.imencode(".jpg", orig_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not is_success:
        return {"is_available": False, "findings": []}

    resaved_bgr = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    # 2. Compute absolute difference between original and resaved
    diff = cv2.absdiff(orig_bgr, resaved_bgr)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

    mean_err = float(np.mean(diff_gray))
    max_err = float(np.max(diff_gray))
    std_err = float(np.std(diff_gray))

    # 3. Amplify error map for human optical inspection
    amplified_gray = np.clip(diff_gray.astype(np.float32) * scale_multiplier, 0, 255).astype(np.uint8)
    heatmap_bgr = cv2.applyColorMap(amplified_gray, cv2.COLORMAP_JET)

    # 4. Detect localized anomaly regions (blocks with error > mean + 3*std)
    anomaly_threshold = mean_err + max(15.0, 2.5 * std_err)
    _, thresh_mask = cv2.threshold(diff_gray, int(anomaly_threshold), 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    suspect_regions: List[Dict[str, int]] = []
    min_area = (h * w) * 0.001  # Ignore tiny noise specks (< 0.1% area)
    max_area = (h * w) * 0.50

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if min_area <= area <= max_area:
            rx, ry, rw, rh = cv2.boundingRect(cnt)
            suspect_regions.append({
                "x": int(rx),
                "y": int(ry),
                "w": int(rw),
                "h": int(rh),
                "area": int(area)
            })

    # Save heatmap image to disk
    os.makedirs(os.path.dirname(output_heatmap_path), exist_ok=True)
    cv2.imwrite(output_heatmap_path, heatmap_bgr)

    # Determine severity and structured findings
    findings = []
    if len(suspect_regions) > 0 and (max_err > 45.0 or mean_err > 8.0):
        # We have clustered compression outliers
        top_region = sorted(suspect_regions, key=lambda r: r["area"], reverse=True)[0]
        severity = "HIGH" if max_err > 60.0 and len(suspect_regions) > 2 else "MEDIUM"
        findings.append({
            "analysis_method": "ELA",
            "severity": severity,
            "region_bbox": {
                "x": top_region["x"],
                "y": top_region["y"],
                "w": top_region["w"],
                "h": top_region["h"]
            },
            "title": f"Compression Anomaly Detected in {len(suspect_regions)} Region(s)",
            "explanation": (
                f"Error Level Analysis identified {len(suspect_regions)} localized region(s) with significantly "
                f"elevated compression error levels (peak difference: {max_err:.1f}, baseline mean: {mean_err:.1f}). "
                "This pattern typically arises when content from a foreign image source or altered digital layer "
                "is pasted onto an existing credential prior to subsequent re-saving."
            ),
            "technical_details": {
                "mean_error": round(mean_err, 2),
                "max_error": round(max_err, 2),
                "std_deviation": round(std_err, 2),
                "scale_multiplier": scale_multiplier,
                "recompression_quality": quality,
                "suspect_regions_count": len(suspect_regions),
                "suspect_regions": suspect_regions[:5]
            },
            "limitations": ELA_LIMITATIONS,
            "recommended_action": (
                "Cross-examine the highlighted region against corresponding VIZ fields and verify whether "
                "security microprint or UV background features show physical interruption."
            )
        })
    else:
        # Uniform compression profile
        findings.append({
            "analysis_method": "ELA",
            "severity": "INFORMATIONAL",
            "region_bbox": None,
            "title": "Homogeneous Error Level Distribution",
            "explanation": (
                f"The document exhibits uniform compression characteristics across all 8x8 DCT macroblocks "
                f"(global mean: {mean_err:.1f}, max: {max_err:.1f}). No localized digital splicing or resaving "
                "discontinuities were detected."
            ),
            "technical_details": {
                "mean_error": round(mean_err, 2),
                "max_error": round(max_err, 2),
                "std_deviation": round(std_err, 2),
                "suspect_regions_count": 0
            },
            "limitations": ELA_LIMITATIONS,
            "recommended_action": "No localized compression anomaly observed; proceed with multi-factor inspection."
        })

    return {
        "is_available": True,
        "mean_error": mean_err,
        "max_error": max_err,
        "heatmap_path": output_heatmap_path,
        "suspect_regions": suspect_regions,
        "findings": findings
    }
