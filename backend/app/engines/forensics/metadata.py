import os
from typing import Dict, Any, List
from PIL import Image, ExifTags

KNOWN_MANIPULATION_SOFTWARE = [
    "photoshop", "canva", "gimp", "paint.net", "coreldraw",
    "affinity", "snapseed", "pixlr", "lightroom", "procreate", "facetune"
]

METADATA_LIMITATIONS = (
    "Metadata tags can be modified, fabricated, or stripped during transit through email and messaging "
    "gateways (e.g., WhatsApp, Telegram). Legitimate document scanners often embed OEM scanning utility "
    "signatures. Metadata findings must be corroborated with optical and cryptographic checks."
)


def run_metadata_inspection(image_path: str) -> Dict[str, Any]:
    """
    Inspects image file EXIF headers and raw metadata for signatures of digital
    photo manipulation software, timestamp anomalies, and device profiles.
    """
    if not os.path.exists(image_path):
        return {"is_available": False, "findings": []}

    exif_data: Dict[str, Any] = {}
    software_detected: List[str] = []
    device_model: str = "Unknown"
    timestamp_info: Dict[str, str] = {}

    try:
        with Image.open(image_path) as img:
            raw_exif = img.getexif()
            if raw_exif:
                for tag_id, val in raw_exif.items():
                    tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                    val_str = str(val).strip()
                    exif_data[tag_name] = val_str

                    if tag_name.lower() in ["software", "imagedescription", "artist", "model", "make"]:
                        for soft in KNOWN_MANIPULATION_SOFTWARE:
                            if soft in val_str.lower():
                                software_detected.append(f"{tag_name}: {val_str}")

                    if tag_name in ["DateTime", "DateTimeOriginal", "DateTimeDigitized"]:
                        timestamp_info[tag_name] = val_str

                    if tag_name in ["Model", "Make"]:
                        device_model = f"{exif_data.get('Make', '')} {exif_data.get('Model', '')}".strip()
    except Exception as e:
        return {
            "is_available": True,
            "error": str(e),
            "findings": [{
                "analysis_method": "METADATA",
                "severity": "INFORMATIONAL",
                "region_bbox": None,
                "title": "EXIF Header Parsing Fault",
                "explanation": f"Unable to parse EXIF metadata table: {str(e)}",
                "technical_details": {"error": str(e)},
                "limitations": METADATA_LIMITATIONS,
                "recommended_action": "Inspect file container manually if required."
            }]
        }

    findings = []
    if software_detected:
        findings.append({
            "analysis_method": "METADATA",
            "severity": "CRITICAL",
            "region_bbox": None,
            "title": "Digital Manipulation Software Signature Detected",
            "explanation": (
                f"Image metadata reveals direct provenance from desktop editing / graphic design software: "
                f"{', '.join(software_detected)}. Official travel credentials are produced by sovereign "
                "passport printers and should not contain consumer digital graphics software headers."
            ),
            "technical_details": {
                "detected_software": software_detected,
                "raw_exif_count": len(exif_data),
                "device_model": device_model,
                "timestamps": timestamp_info
            },
            "limitations": METADATA_LIMITATIONS,
            "recommended_action": "Escalate to Senior Reviewer for physical credential demand."
        })
    elif len(exif_data) == 0:
        findings.append({
            "analysis_method": "METADATA",
            "severity": "INFORMATIONAL",
            "region_bbox": None,
            "title": "Stripped or Absent Metadata",
            "explanation": (
                "The image file does not contain standard camera EXIF metadata. This is typical for files "
                "transferred via web forms, messaging clients, or scanners that strip non-essential headers."
            ),
            "technical_details": {
                "raw_exif_count": 0,
                "device_model": "None"
            },
            "limitations": METADATA_LIMITATIONS,
            "recommended_action": "Standard for web-uploaded documents; corroborate with optical and MRZ checks."
        })
    else:
        findings.append({
            "analysis_method": "METADATA",
            "severity": "INFORMATIONAL",
            "region_bbox": None,
            "title": "Standard Acquisition Device Metadata Present",
            "explanation": (
                f"Document image metadata indicates acquisition from standard capture hardware: "
                f"{device_model or 'Hardware Scanner'}. No prohibited manipulation signatures detected."
            ),
            "technical_details": {
                "device_model": device_model,
                "raw_exif_count": len(exif_data),
                "timestamps": timestamp_info
            },
            "limitations": METADATA_LIMITATIONS,
            "recommended_action": "No metadata anomaly observed."
        })

    return {
        "is_available": True,
        "software_detected": software_detected,
        "device_model": device_model,
        "exif_data": exif_data,
        "findings": findings
    }
