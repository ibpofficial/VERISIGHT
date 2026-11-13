import cv2
import numpy as np
from typing import Dict, Any, List

TEXTURE_LIMITATIONS = (
    "Texture variance can vary across textured paper substrates, security holographic overlays, and "
    "intaglio embossed printing. High-contrast printed lines naturally have higher local variance than flat areas. "
    "Texture findings provide indicative anomalies, not proof of tampering."
)


def run_texture_analysis(image_path: str, grid_rows: int = 8, grid_cols: int = 8) -> Dict[str, Any]:
    """
    Subdivides document surface into grid cells and analyzes high-frequency noise variance
    to detect spliced patches with discordant sensor noise profiles.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        return {"is_available": False, "findings": []}

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Extract high-frequency noise using Laplacian residual
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    noise_variance_grid = np.zeros((grid_rows, grid_cols))

    cell_h = h // grid_rows
    cell_w = w // grid_cols

    anomalous_cells: List[Dict[str, Any]] = []

    for r in range(grid_rows):
        for c in range(grid_cols):
            y1 = r * cell_h
            y2 = (r + 1) * cell_h if r < grid_rows - 1 else h
            x1 = c * cell_w
            x2 = (c + 1) * cell_w if c < grid_cols - 1 else w

            patch = laplacian[y1:y2, x1:x2]
            var = float(np.var(patch))
            noise_variance_grid[r, c] = var

    mean_var = float(np.mean(noise_variance_grid))
    std_var = float(np.std(noise_variance_grid))

    # Identify patches deviating by > 3 standard deviations
    for r in range(grid_rows):
        for c in range(grid_cols):
            val = noise_variance_grid[r, c]
            if val > mean_var + 3.0 * std_var:
                y1 = r * cell_h
                x1 = c * cell_w
                anomalous_cells.append({
                    "row": r,
                    "col": c,
                    "variance": round(val, 2),
                    "bbox": {"x": int(x1), "y": int(y1), "w": int(cell_w), "h": int(cell_h)}
                })

    findings = []
    if len(anomalous_cells) >= 2:
        top_cell = sorted(anomalous_cells, key=lambda x: x["variance"], reverse=True)[0]
        findings.append({
            "analysis_method": "TEXTURE",
            "severity": "MEDIUM",
            "region_bbox": top_cell["bbox"],
            "title": f"Inconsistent Surface Texture in {len(anomalous_cells)} Grid Sector(s)",
            "explanation": (
                f"High-frequency residual noise analysis identified {len(anomalous_cells)} localized sector(s) "
                f"with abnormal noise variance (peak: {top_cell['variance']:.1f} vs mean: {mean_var:.1f}). "
                "Such variance spikes often indicate digital copy-paste overlays or retouching with different "
                "grain profiles than the underlying substrate."
            ),
            "technical_details": {
                "grid_dimensions": f"{grid_rows}x{grid_cols}",
                "mean_variance": round(mean_var, 2),
                "std_variance": round(std_var, 2),
                "anomalous_cells_count": len(anomalous_cells),
                "anomalous_cells": anomalous_cells[:4]
            },
            "limitations": TEXTURE_LIMITATIONS,
            "recommended_action": "Inspect flagged sector under physical or optical magnification."
        })
    else:
        findings.append({
            "analysis_method": "TEXTURE",
            "severity": "INFORMATIONAL",
            "region_bbox": None,
            "title": "Homogeneous High-Frequency Surface Texture",
            "explanation": (
                f"Substrate texture analysis demonstrated consistent sensor grain across all {grid_rows*grid_cols} "
                f"spatial grid sectors (mean variance: {mean_var:.1f}, std dev: {std_var:.1f}). No localized "
                "texture splicing detected."
            ),
            "technical_details": {
                "mean_variance": round(mean_var, 2),
                "std_variance": round(std_var, 2)
            },
            "limitations": TEXTURE_LIMITATIONS,
            "recommended_action": "Standard consistent texture baseline."
        })

    return {
        "is_available": True,
        "mean_variance": mean_var,
        "std_variance": std_var,
        "anomalous_cells": anomalous_cells,
        "findings": findings
    }
