import re
from typing import List, Dict, Any, Optional, Tuple
from backend.app.engines.mrz.check_digits import verify_check_digit, calculate_mrz_check_digit

ALPHA_TO_NUMERIC = {
    'O': '0', 'D': '0', 'Q': '0',
    'I': '1', 'L': '1',
    'Z': '2',
    'S': '5',
    'B': '8'
}

NUMERIC_TO_ALPHA = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '5': 'S',
    '8': 'B'
}


def normalize_numeric_segment(raw_segment: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Substitutes common OCR alphabetical misreads in strictly numeric positions.
    Returns normalized string and list of explicit correction records.
    """
    corrections = []
    chars = list(raw_segment)
    for i, c in enumerate(chars):
        if c in ALPHA_TO_NUMERIC:
            norm_c = ALPHA_TO_NUMERIC[c]
            chars[i] = norm_c
            corrections.append({
                "index": i,
                "raw_char": c,
                "corrected_char": norm_c,
                "type": "ALPHA_TO_NUMERIC_OCR_CORRECTION"
            })
    return "".join(chars), corrections


def verify_with_auto_correction(
    raw_data: str,
    raw_check_digit: str,
    field_name: str
) -> Tuple[str, str, bool, List[Dict[str, Any]]]:
    """
    Verifies check digit. If check fails, tests position-aware OCR normalization.
    If normalization resolves the check digit, returns the corrected string with explicit logs.
    """
    # 1. Try directly
    if verify_check_digit(raw_data, raw_check_digit):
        return raw_data, raw_check_digit, True, []

    # 2. Try normalized numeric data
    norm_data, data_corrs = normalize_numeric_segment(raw_data)
    norm_check, check_corrs = normalize_numeric_segment(raw_check_digit)

    if verify_check_digit(norm_data, norm_check):
        all_corrs = []
        for c in data_corrs:
            c["field"] = field_name
            c["note"] = "OCR-corrected check digit validated"
            all_corrs.append(c)
        for c in check_corrs:
            c["field"] = f"{field_name}_check_digit"
            c["note"] = "OCR-corrected check digit validated"
            all_corrs.append(c)
        return norm_data, norm_check, True, all_corrs

    # Still invalid
    return raw_data, raw_check_digit, False, []


def parse_mrz_td3(line1: str, line2: str) -> Dict[str, Any]:
    """
    Parses ICAO Doc 9303 TD3 Passports (2 lines of 44 characters).
    """
    line1 = line1.ljust(44, '<')[:44]
    line2 = line2.ljust(44, '<')[:44]

    doc_code = line1[0:2].replace('<', '')
    issuing_country = line1[2:5].replace('<', '')

    name_field = line1[5:44]
    name_parts = name_field.split('<<')
    surname = name_parts[0].replace('<', ' ').strip()
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""

    all_corrections: List[Dict[str, Any]] = []

    # Document Number (Line 2: 0..8, check 9)
    doc_raw = line2[0:9]
    doc_chk = line2[9]
    doc_clean, doc_chk_clean, is_doc_valid, corrs = verify_with_auto_correction(doc_raw, doc_chk, "document_number")
    all_corrections.extend(corrs)
    document_number = doc_clean.replace('<', '').strip()

    nationality = line2[10:13].replace('<', '')

    # DOB (Line 2: 13..18, check 19)
    dob_raw = line2[13:19]
    dob_chk = line2[19]
    dob_clean, dob_chk_clean, is_dob_valid, corrs = verify_with_auto_correction(dob_raw, dob_chk, "date_of_birth")
    all_corrections.extend(corrs)

    sex = line2[20].replace('<', 'X')

    # Expiry (Line 2: 21..26, check 27)
    exp_raw = line2[21:27]
    exp_chk = line2[27]
    exp_clean, exp_chk_clean, is_exp_valid, corrs = verify_with_auto_correction(exp_raw, exp_chk, "expiry_date")
    all_corrections.extend(corrs)

    optional_raw = line2[28:42]
    optional_data = optional_raw.replace('<', '').strip()
    optional_check = line2[42]

    # Composite check
    comp_chk = line2[43]
    composite_data = line2[0:10] + line2[13:20] + line2[21:43]
    is_composite_valid = verify_check_digit(composite_data, comp_chk)
    if not is_composite_valid:
        norm_comp, _, is_composite_valid, _ = verify_with_auto_correction(composite_data, comp_chk, "composite")

    return {
        "format": "TD3",
        "doc_type_code": doc_code or "P",
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "document_number": document_number,
        "nationality": nationality,
        "dob": dob_clean,
        "sex": sex,
        "expiry_date": exp_clean,
        "optional_data": optional_data or None,
        "doc_number_check": is_doc_valid,
        "dob_check": is_dob_valid,
        "expiry_check": is_exp_valid,
        "composite_check": is_composite_valid,
        "ocr_corrections": all_corrections,
        "raw_lines": [line1, line2],
    }


def parse_mrz_td2(line1: str, line2: str) -> Dict[str, Any]:
    """
    Parses ICAO Doc 9303 TD2 Official Travel Documents (2 lines of 36 characters).
    """
    line1 = line1.ljust(36, '<')[:36]
    line2 = line2.ljust(36, '<')[:36]

    doc_code = line1[0:2].replace('<', '')
    issuing_country = line1[2:5].replace('<', '')

    name_field = line1[5:36]
    name_parts = name_field.split('<<')
    surname = name_parts[0].replace('<', ' ').strip()
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""

    all_corrections: List[Dict[str, Any]] = []

    doc_raw = line2[0:9]
    doc_chk = line2[9]
    doc_clean, _, is_doc_valid, corrs = verify_with_auto_correction(doc_raw, doc_chk, "document_number")
    all_corrections.extend(corrs)
    document_number = doc_clean.replace('<', '').strip()

    nationality = line2[10:13].replace('<', '')

    dob_raw = line2[13:19]
    dob_chk = line2[19]
    dob_clean, _, is_dob_valid, corrs = verify_with_auto_correction(dob_raw, dob_chk, "date_of_birth")
    all_corrections.extend(corrs)

    sex = line2[20].replace('<', 'X')

    exp_raw = line2[21:27]
    exp_chk = line2[27]
    exp_clean, _, is_exp_valid, corrs = verify_with_auto_correction(exp_raw, exp_chk, "expiry_date")
    all_corrections.extend(corrs)

    optional_raw = line2[28:35]
    optional_data = optional_raw.replace('<', '').strip()
    comp_chk = line2[35]

    composite_data = line2[0:10] + line2[13:20] + line2[21:35]
    is_composite_valid = verify_check_digit(composite_data, comp_chk)

    return {
        "format": "TD2",
        "doc_type_code": doc_code or "I",
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "document_number": document_number,
        "nationality": nationality,
        "dob": dob_clean,
        "sex": sex,
        "expiry_date": exp_clean,
        "optional_data": optional_data or None,
        "doc_number_check": is_doc_valid,
        "dob_check": is_dob_valid,
        "expiry_check": is_exp_valid,
        "composite_check": is_composite_valid,
        "ocr_corrections": all_corrections,
        "raw_lines": [line1, line2],
    }


def parse_mrz_td1(line1: str, line2: str, line3: str) -> Dict[str, Any]:
    """
    Parses ICAO Doc 9303 TD1 Identity Cards (3 lines of 30 characters).
    """
    line1 = line1.ljust(30, '<')[:30]
    line2 = line2.ljust(30, '<')[:30]
    line3 = line3.ljust(30, '<')[:30]

    doc_code = line1[0:2].replace('<', '')
    issuing_country = line1[2:5].replace('<', '')

    all_corrections: List[Dict[str, Any]] = []

    # Document number: Line 1: 5..14 (9 chars), check digit @ 14
    doc_raw = line1[5:14]
    doc_chk = line1[14]
    doc_clean, _, is_doc_valid, corrs = verify_with_auto_correction(doc_raw, doc_chk, "document_number")
    all_corrections.extend(corrs)
    document_number = doc_clean.replace('<', '').strip()

    # Line 2: DOB (0..6), check @ 6
    dob_raw = line2[0:6]
    dob_chk = line2[6]
    dob_clean, _, is_dob_valid, corrs = verify_with_auto_correction(dob_raw, dob_chk, "date_of_birth")
    all_corrections.extend(corrs)

    sex = line2[7].replace('<', 'X')

    # Line 2: Expiry (8..14), check @ 14
    exp_raw = line2[8:14]
    exp_chk = line2[14]
    exp_clean, _, is_exp_valid, corrs = verify_with_auto_correction(exp_raw, exp_chk, "expiry_date")
    all_corrections.extend(corrs)

    nationality = line2[15:18].replace('<', '')
    optional_data = line2[18:29].replace('<', '').strip()
    comp_chk = line2[29]

    # Composite check covering line1[5:30] + line2[0:7] + line2[8:15] + line2[18:29]
    composite_data = line1[5:30] + line2[0:7] + line2[8:15] + line2[18:29]
    is_composite_valid = verify_check_digit(composite_data, comp_chk)

    # Line 3: Name
    name_parts = line3.split('<<')
    surname = name_parts[0].replace('<', ' ').strip()
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""

    return {
        "format": "TD1",
        "doc_type_code": doc_code or "I",
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "document_number": document_number,
        "nationality": nationality,
        "dob": dob_clean,
        "sex": sex,
        "expiry_date": exp_clean,
        "optional_data": optional_data or None,
        "doc_number_check": is_doc_valid,
        "dob_check": is_dob_valid,
        "expiry_check": is_exp_valid,
        "composite_check": is_composite_valid,
        "ocr_corrections": all_corrections,
        "raw_lines": [line1, line2, line3],
    }


def parse_mrz(lines: List[str]) -> Dict[str, Any]:
    """Auto-detects format (TD3, TD2, TD1) based on line count and line lengths."""
    cleaned = [re.sub(r'[^A-Z0-9<]', '', l.strip().upper()) for l in lines if l.strip()]
    if len(cleaned) == 3 or (len(cleaned) > 2 and len(cleaned[0]) <= 32):
        return parse_mrz_td1(cleaned[0], cleaned[1], cleaned[2])
    elif len(cleaned) >= 2:
        if len(cleaned[0]) <= 38:
            return parse_mrz_td2(cleaned[0], cleaned[1])
        return parse_mrz_td3(cleaned[0], cleaned[1])
    else:
        raise ValueError(f"Insufficient MRZ lines for parsing: {len(cleaned)} lines found.")


def cross_check_mrz_with_viz(
    mrz_data: Dict[str, Any],
    viz_fields: Dict[str, Any],
    viz_confidences: Optional[Dict[str, Optional[float]]] = None
) -> Dict[str, Any]:
    """
    Compares decoded MRZ attributes with visual printed fields extracted by OCR.
    Enforces discrete states:
    - MATCH: printed field and MRZ attribute agree with solid confidence
    - MISMATCH: printed field directly contradicts MRZ attribute
    - UNAVAILABLE: either printed or MRZ field is missing / null
    - UNCERTAIN: OCR confidence is low (< 0.65), precluding definitive mismatch flag
    """
    matches: Dict[str, bool] = {}
    detailed_status: Dict[str, str] = {}
    discrepancies: List[Dict[str, Any]] = []

    conf_dict = viz_confidences or {}

    def evaluate_pair(field_name: str, viz_val: Optional[str], mrz_val: Optional[str]):
        if not viz_val or not mrz_val:
            detailed_status[field_name] = "UNAVAILABLE"
            matches[field_name] = False
            return

        conf = conf_dict.get(field_name)
        v_clean = re.sub(r'[^A-Z0-9]', '', str(viz_val).upper())
        m_clean = re.sub(r'[^A-Z0-9]', '', str(mrz_val).upper())

        is_equal = (v_clean == m_clean) or (v_clean in m_clean) or (m_clean in v_clean)

        if is_equal:
            detailed_status[field_name] = "MATCH"
            matches[field_name] = True
        else:
            if conf is not None and conf < 0.65:
                detailed_status[field_name] = "UNCERTAIN"
                matches[field_name] = False
            else:
                detailed_status[field_name] = "MISMATCH"
                matches[field_name] = False
                discrepancies.append({
                    "field": field_name,
                    "viz_value": viz_val,
                    "mrz_value": mrz_val,
                    "message": f"Cross-check mismatch: printed '{viz_val}' contradicts MRZ '{mrz_val}'"
                })

    evaluate_pair("document_number", viz_fields.get("document_number"), mrz_data.get("document_number"))
    evaluate_pair("surname", viz_fields.get("surname"), mrz_data.get("surname"))
    evaluate_pair("given_names", viz_fields.get("given_names"), mrz_data.get("given_names"))
    evaluate_pair("nationality", viz_fields.get("nationality"), mrz_data.get("nationality"))

    return {
        "matches": matches,
        "detailed_status": detailed_status,
        "discrepancies": discrepancies,
        "is_consistent": len(discrepancies) == 0
    }
