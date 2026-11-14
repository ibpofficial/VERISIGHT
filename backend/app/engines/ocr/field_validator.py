import re
from datetime import datetime
from typing import Optional, Tuple
from backend.app.models import ValidationStatus


def parse_date_with_century_inference(
    date_str: str,
    is_expiry: bool = False
) -> Tuple[Optional[datetime], str]:
    """
    Parses dates across multiple standards with explicit century inference:
    Formats supported:
    - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    - DD MMM YYYY (e.g. 14 MAY 1988)
    - YYMMDD (standard ICAO 9303 MRZ 6-digit date)
    
    Century inference rules:
    - Expiry dates: 2-digit YY maps to 20YY (travel credentials expire in the 21st century).
    - DOB: if 20YY > current_year, maps to 19YY (birth date cannot be in the future).
    Returns (parsed_datetime, inference_note).
    """
    if not date_str:
        return None, "NO_DATA"

    cleaned = date_str.strip()
    current_year = datetime.now().year
    current_yy = current_year % 100

    # 1. 6-digit ICAO MRZ format: YYMMDD
    if re.match(r'^\d{6}$', cleaned):
        try:
            yy = int(cleaned[0:2])
            mm = int(cleaned[2:4])
            dd = int(cleaned[4:6])

            if mm < 1 or mm > 12 or dd < 1 or dd > 31:
                return None, "INVALID_DAY_MONTH_RANGE"

            if is_expiry:
                full_year = 2000 + yy
                method = "EXPLICIT_EXPIRY_21ST_CENTURY_INFERENCE"
            else:
                # Birth date: cannot be in the future
                if yy <= current_yy:
                    full_year = 2000 + yy
                    method = "EXPLICIT_DOB_21ST_CENTURY_INFERENCE"
                else:
                    full_year = 1900 + yy
                    method = "EXPLICIT_DOB_20TH_CENTURY_INFERENCE"

            dt = datetime(full_year, mm, dd)
            return dt, method
        except ValueError as ve:
            return None, f"INVALID_DATE_VALUE: {str(ve)}"

    # 2. 4-digit year full calendar formats
    full_formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y",
        "%d %b %Y", "%d %B %Y",
        "%Y/%m/%d", "%Y-%m-%d", "%d%m%Y"
    ]
    for fmt in full_formats:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt, "EXPLICIT_4_DIGIT_YEAR"
        except ValueError:
            continue

    return None, "UNRECOGNIZED_FORMAT"


def parse_date_flexible(date_str: str) -> Optional[datetime]:
    dt, _ = parse_date_with_century_inference(date_str)
    return dt


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

    # Confidence floor check
    if confidence is not None and confidence < 0.45:
        return ValidationStatus.LOW_CONFIDENCE

    # Field-specific format checks
    if field_name in ("date_of_birth", "dob"):
        dt, note = parse_date_with_century_inference(val, is_expiry=False)
        if not dt:
            return ValidationStatus.INVALID_FORMAT
        if dt > datetime.now():
            return ValidationStatus.INVALID_FORMAT

    elif field_name in ("expiry_date", "date_of_expiry"):
        dt, note = parse_date_with_century_inference(val, is_expiry=True)
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
