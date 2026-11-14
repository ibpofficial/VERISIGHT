import cv2
import numpy as np
import os
from typing import Dict, Any, Tuple, List, Optional


def order_points(pts: np.ndarray) -> np.ndarray:
    """Orders 4 coordinates: [top-left, top-right, bottom-right, bottom-left]."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def correct_perspective_contour(img: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    Detects 4-point document contour in background and performs perspective warp rectification.
    """
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4 and cv2.contourArea(c) > (w * h * 0.25):
            pts = approx.reshape(4, 2)
            rect = order_points(pts)
            (tl, tr, br, bl) = rect

            width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            max_w = max(int(width_a), int(width_b))

            height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            max_h = max(int(height_a), int(height_b))

            if max_w > 100 and max_h > 100:
                dst = np.array([
                    [0, 0],
                    [max_w - 1, 0],
                    [max_w - 1, max_h - 1],
                    [0, max_h - 1]
                ], dtype="float32")

                M = cv2.getPerspectiveTransform(rect, dst)
                warped = cv2.warpPerspective(img, M, (max_w, max_h))
                return warped, True

    return img, False


def preprocess_document_image(
    input_path: str, 
    output_dir: str, 
    orientation_hint: int = 0
) -> Tuple[str, Dict[str, Any]]:
    """
    Non-destructive document image rectification and normalization:
    1. Rotation: fixes 90/180/270 deg misorientations
    2. Perspective Rectification: 4-point quadrilateral contour warp
    3. Deskew: detects dominant text baseline angle via Hough Lines
    4. CLAHE: normalizes contrast across varied illumination gradients
    5. Denoise: bilateral filter preserving sharp glyph edges
    """
    img = cv2.imread(input_path)
    if img is None:
        raise ValueError(f"Unable to read image at {input_path}")

    # 1. Orientation correction if required
    if orientation_hint == 90:
        img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif orientation_hint == 180:
        img = cv2.rotate(img, cv2.ROTATE_180)
    elif orientation_hint == 270:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

    # 2. Perspective warp if document boundary found
    img, perspective_applied = correct_perspective_contour(img)

    h, w = img.shape[:2]

    # 3. Deskew via Hough Line Transform
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=w // 6, maxLineGap=20)

    skew_angle = 0.0
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines:
            line_data = line.reshape(-1)
            if len(line_data) >= 4:
                x1, y1, x2, y2 = int(line_data[0]), int(line_data[1]), int(line_data[2]), int(line_data[3])
                dx = x2 - x1
                dy = y2 - y1
                if dx != 0:
                    ang = np.degrees(np.arctan2(dy, dx))
                    if -45 < ang < 45:
                        angles.append(ang)
        if len(angles) > 3:
            skew_angle = float(np.median(angles))

    # Apply affine rotation if skew is significant (> 0.5 degrees)
    if abs(skew_angle) > 0.5 and abs(skew_angle) < 45.0:
        center = (w // 2, h // 2)
        rot_mat = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
        img = cv2.warpAffine(img, rot_mat, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # 4. Contrast Normalization via CLAHE on LAB luminance
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    lab_norm = cv2.merge((l_clahe, a, b))
    img_norm = cv2.cvtColor(lab_norm, cv2.COLOR_LAB2BGR)

    # 5. Edge-preserving Denoising
    denoised = cv2.bilateralFilter(img_norm, d=5, sigmaColor=50, sigmaSpace=50)

    # Save processed image to designated output directory
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(input_path)
    processed_filename = f"processed_{base_name}"
    processed_path = os.path.join(output_dir, processed_filename)

    cv2.imwrite(processed_path, denoised)

    metadata = {
        "applied_rotation": orientation_hint,
        "perspective_applied": perspective_applied,
        "detected_skew_angle": round(skew_angle, 2),
        "deskew_applied": abs(skew_angle) > 0.5,
        "clahe_applied": True,
        "denoising_applied": True,
        "output_dimensions": {"width": w, "height": h},
    }

    return processed_path, metadata
