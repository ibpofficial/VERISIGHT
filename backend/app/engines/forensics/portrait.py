import os
import cv2
import numpy as np
from typing import Dict, Any, List

PORTRAIT_LIMITATIONS = (
    "Portrait edge gradients can be affected by standard document printing techniques such as laser engraving, "
    "ghost portrait watermark overlays, or variable laminate gloss reflections. "
    "Portrait boundary alerts are evidentiary indicators requiring forensic magnification review."
)


def run_portrait_analysis(image_path: str) -> Dict[str, Any]:
    """
    Locates portrait region and inspects perimeter boundary edges for abrupt gradient steps,
    digital feathering, or paste seam artifacts.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        return {"is_available": False, "findings": []}

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 1. Standard Passport Portrait Zone (typically left side: x: 0.05..0.45, y: 0.15..0.75)
    # Also attempt Haar cascade face detection if available
    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    faces = []
    if os.path.exists(face_cascade_path):
        cascade = cv2.CascadeClassifier(face_cascade_path)
        detected = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(int(w*0.1), int(h*0.1)))
        if len(detected) > 0:
            faces = detected

    portrait_bbox = None
    if len(faces) > 0:
        fx, fy, fw, fh = faces[0]
        # Expand slightly to cover full photo frame
        margin_x = int(fw * 0.2)
        margin_y = int(fh * 0.25)
        portrait_bbox = {
            "x": max(0, int(fx - margin_x)),
            "y": max(0, int(fy - margin_y)),
            "w": min(w - int(fx - margin_x), int(fw + 2 * margin_x)),
            "h": min(h - int(fy - margin_y), int(fh + 2 * margin_y))
        }
    else:
        # Default ICAO passport left portrait window heuristic
        portrait_bbox = {
            "x": int(w * 0.05),
            "y": int(h * 0.18),
            "w": int(w * 0.35),
            "h": int(h * 0.55)
        }

    # 2. Inspect perimeter boundary gradient of portrait box
    bx = portrait_bbox["x"]
    by = portrait_bbox["y"]
    bw = portrait_bbox["w"]
    bh = portrait_bbox["h"]

    # Sample perimeter strips (outer vs inner ring)
    border_thickness = max(3, int(min(bw, bh) * 0.04))
    
    # Gradient magnitude along perimeter
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    grad_mag = cv2.magnitude(sobelx, sobely)

    # Perimeter edge sharpness
    top_edge = grad_mag[max(0, by - border_thickness):by + border_thickness, bx:bx + bw]
    bottom_edge = grad_mag[by + bh - border_thickness:min(h, by + bh + border_thickness), bx:bx + bw]
    left_edge = grad_mag[by:by + bh, max(0, bx - border_thickness):bx + border_thickness]
    right_edge = grad_mag[by:by + bh, bx + bw - border_thickness:min(w, bx + bw + border_thickness)]

    edge_means = [float(np.mean(e)) for e in [top_edge, bottom_edge, left_edge, right_edge] if e.size > 0]
    avg_perimeter_gradient = float(np.mean(edge_means)) if edge_means else 0.0

    # High abrupt step across all 4 borders indicates a hard-pasted rectangular photo
    findings = []
    if avg_perimeter_gradient > 65.0:
        findings.append({
            "analysis_method": "PORTRAIT",
            "severity": "HIGH",
            "region_bbox": portrait_bbox,
            "title": "Abrupt Portrait Boundary Discontinuity Detected",
            "explanation": (
                f"Boundary gradient analysis identified high edge sharpness around the portrait perimeter "
                f"(mean gradient magnitude: {avg_perimeter_gradient:.1f}). In genuine modern travel documents, "
                "the portrait is laser-integrated directly into the underlying security background guilloche. "
                "An unbroken, sharp step edge indicates a physical photo-substitution or digital paste layer."
            ),
            "technical_details": {
                "portrait_bbox": portrait_bbox,
                "mean_perimeter_gradient": round(avg_perimeter_gradient, 2),
                "edge_means": [round(m, 2) for m in edge_means]
            },
            "limitations": PORTRAIT_LIMITATIONS,
            "recommended_action": "Check for physical laminate disturbance or microprint continuity across photo boundary."
        })
    else:
        findings.append({
            "analysis_method": "PORTRAIT",
            "severity": "INFORMATIONAL",
            "region_bbox": portrait_bbox,
            "title": "Continuous Background-to-Portrait Transition",
            "explanation": (
                f"Portrait boundary inspection verified continuous background transition with no anomalous "
                f"rectangular paste seam (mean border gradient: {avg_perimeter_gradient:.1f}). "
                "Pattern exhibits standard integrated printing characteristics."
            ),
            "technical_details": {
                "portrait_bbox": portrait_bbox,
                "mean_perimeter_gradient": round(avg_perimeter_gradient, 2)
            },
            "limitations": PORTRAIT_LIMITATIONS,
            "recommended_action": "Portrait perimeter integration within normal parameters."
        })

    return {
        "is_available": True,
        "portrait_bbox": portrait_bbox,
        "avg_perimeter_gradient": avg_perimeter_gradient,
        "findings": findings
    }
