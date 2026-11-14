import re
from datetime import datetime
from typing import Optional
from backend.app.models import ValidationStatus


def parse_date_flexible(date_str: str) -> Optional[datetime]:
    """Attempts to parse common passport and identity credential date strings."""
    if not date_str:
        return None
    cleaned = date_str.strip()
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%d %b %Y", "%d %B %Y",
        "%Y/%m/%d", "%Y-%m-%d",
        "%d%m%Y", "%y%m%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue
    return None


def compute_field_validation_status(
    field_name: str,
    value: Optional[str],
    confidence: Optional[float],
    mrz_value: Optional[str] = None
) -> ValidationStatus:
    """
    Computes deterministic field validation status without hardcoded defaults:
    - MISSING: field value is null or empty string
    - LOW_CONFIDENCE: OCR engine confidence falls below threshold
    - INVALID_FORMAT: field format, date, or syntax violates specifications
    - INVALID: printed field directly contradicts verified MRZ value
    - VALID: format is sound and confidence is acceptable
    """
    if value is None or str(value).strip() == "":
        return ValidationStatus.MISSING

    val = str(value).strip()

    # Confidence check
    if confidence is not None and confidence < 0.45:
        return ValidationStatus.LOW_CONFIDENCE

    # Field-specific format checks
    if field_name in ("date_of_birth", "dob"):
        dt = parse_date_flexible(val)
        if not dt:
            return ValidationStatus.INVALID_FORMAT
        # DOB must be in the past
        if dt > datetime.now():
            return ValidationStatus.INVALID_FORMAT

    elif field_name in ("expiry_date", "date_of_expiry"):
        dt = parse_date_flexible(val)
        if not dt:
            return ValidationStatus.INVALID_FORMAT

    elif field_name == "document_number":
        cleaned_doc = re.sub(r'[\s\-]', '', val.upper())
        if not re.match(r'^[A-Z0-9]{6,12}$', cleaned_doc):
            return ValidationStatus.INVALID_FORMAT

    elif field_name == "sex":
        cleaned_sex = val.upper().strip()
        if cleaned_sex not in ("M", "F", "X", "MALE", "FEMALE"):
            return ValidationStatus.INVALID_FORMAT

    elif field_name in ("nationality", "issuing_state"):
        cleaned_state = re.sub(r'[^A-Z]', '', val.upper().strip())
        if len(cleaned_state) < 2 or any(char.isdigit() for char in val):
            return ValidationStatus.INVALID_FORMAT

    # MRZ cross-check contradiction check
    if mrz_value:
        norm_viz = re.sub(r'[^A-Z0-9]', '', val.upper())
        norm_mrz = re.sub(r'[^A-Z0-9]', '', str(mrz_value).upper())
        if norm_viz and norm_mrz and norm_viz != norm_mrz:
            return ValidationStatus.INVALID

    if confidence is not None and confidence < 0.65:
        return ValidationStatus.LOW_CONFIDENCE

    return ValidationStatus.VALID
