import cv2
import numpy as np
import os
from typing import Dict, Any, Tuple


def preprocess_document_image(
    input_path: str, 
    output_dir: str, 
    orientation_hint: int = 0
) -> Tuple[str, Dict[str, Any]]:
    """
    Non-destructive document image rectification and normalization:
    1. Rotation: fixes 90/180/270 deg misorientations
    2. Deskew: detects dominant text baseline angle via Hough Lines
    3. CLAHE: normalizes contrast across varied illumination gradients
    4. Denoise: bilateral filter preserving text edges
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

    h, w = img.shape[:2]

    # 2. Deskew via Hough Line Transform
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

    # 3. Contrast Normalization via CLAHE on LAB luminance
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_clahe = clahe.apply(l)
    lab_norm = cv2.merge((l_clahe, a, b))
    img_norm = cv2.cvtColor(lab_norm, cv2.COLOR_LAB2BGR)

    # 4. Edge-preserving Denoising
    denoised = cv2.bilateralFilter(img_norm, d=5, sigmaColor=50, sigmaSpace=50)

    # Save processed image to designated output directory
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(input_path)
    processed_filename = f"processed_{base_name}"
    processed_path = os.path.join(output_dir, processed_filename)

    cv2.imwrite(processed_path, denoised)

    metadata = {
        "applied_rotation": orientation_hint,
        "detected_skew_angle": round(skew_angle, 2),
        "deskew_applied": abs(skew_angle) > 0.5,
        "clahe_applied": True,
        "denoising_applied": True,
        "output_dimensions": {"width": w, "height": h},
    }

    return processed_path, metadata
