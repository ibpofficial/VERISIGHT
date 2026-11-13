import os
from typing import Dict, Any, List

from backend.app.engines.forensics.ela import run_error_level_analysis
from backend.app.engines.forensics.metadata import run_metadata_inspection
from backend.app.engines.forensics.texture import run_texture_analysis
from backend.app.engines.forensics.alignment import run_alignment_analysis
from backend.app.engines.forensics.portrait import run_portrait_analysis


def run_full_forensic_suite(
    raw_path: str,
    processed_path: str,
    output_heatmap_path: str
) -> Dict[str, Any]:
    """
    Executes the 5-pillar digital forensics inspection suite on the document:
    1. Error Level Analysis (ELA) with Heatmap Generation
    2. Header & Software Provenance Metadata Inspection
    3. High-Frequency Surface Texture Variance
    4. Text Line Typographic Alignment & Pitch
    5. Portrait Perimeter Boundary Discontinuity
    """
    results: Dict[str, Any] = {
        "ela": {},
        "metadata": {},
        "texture": {},
        "alignment": {},
        "portrait": {},
        "all_findings": []
    }

    # 1. ELA
    try:
        ela_res = run_error_level_analysis(processed_path, output_heatmap_path)
        results["ela"] = ela_res
        results["all_findings"].extend(ela_res.get("findings", []))
    except Exception as e:
        results["ela"] = {"is_available": False, "error": str(e)}

    # 2. Metadata (run on original raw bytes)
    try:
        meta_res = run_metadata_inspection(raw_path)
        results["metadata"] = meta_res
        results["all_findings"].extend(meta_res.get("findings", []))
    except Exception as e:
        results["metadata"] = {"is_available": False, "error": str(e)}

    # 3. Texture
    try:
        tex_res = run_texture_analysis(processed_path)
        results["texture"] = tex_res
        results["all_findings"].extend(tex_res.get("findings", []))
    except Exception as e:
        results["texture"] = {"is_available": False, "error": str(e)}

    # 4. Alignment
    try:
        align_res = run_alignment_analysis(processed_path)
        results["alignment"] = align_res
        results["all_findings"].extend(align_res.get("findings", []))
    except Exception as e:
        results["alignment"] = {"is_available": False, "error": str(e)}

    # 5. Portrait
    try:
        port_res = run_portrait_analysis(processed_path)
        results["portrait"] = port_res
        results["all_findings"].extend(port_res.get("findings", []))
    except Exception as e:
        results["portrait"] = {"is_available": False, "error": str(e)}

    return results
