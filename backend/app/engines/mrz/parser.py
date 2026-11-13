from typing import List, Dict, Any, Optional
from backend.app.engines.mrz.check_digits import verify_check_digit, calculate_mrz_check_digit


def parse_mrz_td3(line1: str, line2: str) -> Dict[str, Any]:
    """
    Parses ICAO Doc 9303 Part 4 Machine Readable Passports (TD3: 2 lines of 44 characters).
    Line 1:
      0..1: Document code (P<, PO, etc.)
      2..4: Issuing state (3 chars)
      5..43: Name (Surname<<Given<Names)
    Line 2:
      0..8: Document number (9 chars)
      9: Document number check digit
      10..12: Nationality (3 chars)
      13..18: Date of birth (YYMMDD)
      19: Date of birth check digit
      20: Sex (M, F, X, <)
      21..26: Date of expiry (YYMMDD)
      27: Date of expiry check digit
      28..41: Personal number / Optional data (14 chars)
      42: Optional data check digit (or '<')
      43: Composite check digit
    """
    # Pad to 44 characters if needed
    line1 = line1.ljust(44, '<')[:44]
    line2 = line2.ljust(44, '<')[:44]

    doc_code = line1[0:2].replace('<', '')
    issuing_country = line1[2:5].replace('<', '')

    # Parse names (Surname<<Given<Names)
    name_field = line1[5:44]
    name_parts = name_field.split('<<')
    surname = name_parts[0].replace('<', ' ').strip()
    given_names = name_parts[1].replace('<', ' ').strip() if len(name_parts) > 1 else ""

    doc_number_raw = line2[0:9]
    doc_number = doc_number_raw.replace('<', '').strip()
    doc_num_check = line2[9]

    nationality = line2[10:13].replace('<', '')
    dob_raw = line2[13:19]
    dob_check = line2[19]

    sex = line2[20].replace('<', 'X')
    expiry_raw = line2[21:27]
    expiry_check = line2[27]

    optional_raw = line2[28:42]
    optional_data = optional_raw.replace('<', '').strip()
    optional_check = line2[42]

    composite_check = line2[43]

    # Verify check digits
    is_doc_num_valid = verify_check_digit(doc_number_raw, doc_num_check)
    is_dob_valid = verify_check_digit(dob_raw, dob_check)
    is_expiry_valid = verify_check_digit(expiry_raw, expiry_check)

    # Optional check digit: if optional_check is a digit, verify it
    is_optional_valid = True
    if optional_check.isdigit():
        is_optional_valid = verify_check_digit(optional_raw, optional_check)

    # Composite check: covers line2[0:10] + line2[13:20] + line2[21:43]
    composite_data = line2[0:10] + line2[13:20] + line2[21:43]
    is_composite_valid = verify_check_digit(composite_data, composite_check)

    return {
        "format": "TD3",
        "doc_type_code": doc_code or "P",
        "issuing_country": issuing_country,
        "surname": surname,
        "given_names": given_names,
        "document_number": doc_number,
        "nationality": nationality,
        "dob": dob_raw,
        "sex": sex,
        "expiry_date": expiry_raw,
        "optional_data": optional_data or None,
        "doc_number_check": is_doc_num_valid,
        "dob_check": is_dob_valid,
        "expiry_check": is_expiry_valid,
        "composite_check": is_composite_valid,
        "raw_lines": [line1, line2],
    }


def cross_check_mrz_with_viz(mrz_data: Dict[str, Any], viz_fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Compares decoded MRZ attributes with visual printed fields extracted by OCR:
    Returns dict of matched status and explicit discrepancy warnings.
    """
    matches: Dict[str, bool] = {}
    discrepancies: List[Dict[str, Any]] = []

    # 1. Document Number
    viz_doc = viz_fields.get("document_number", "").replace(" ", "").upper()
    mrz_doc = mrz_data.get("document_number", "").replace(" ", "").upper()
    if viz_doc and mrz_doc:
        matched = (viz_doc == mrz_doc)
        matches["document_number"] = matched
        if not matched:
            discrepancies.append({
                "field": "document_number",
                "viz_value": viz_doc,
                "mrz_value": mrz_doc,
                "message": f"Document number discrepancy: printed '{viz_doc}' vs MRZ '{mrz_doc}'"
            })

    # 2. Surname
    viz_surname = viz_fields.get("surname", "").replace(" ", "").upper()
    mrz_surname = mrz_data.get("surname", "").replace(" ", "").upper()
    if viz_surname and mrz_surname:
        matched = (viz_surname in mrz_surname or mrz_surname in viz_surname)
        matches["surname"] = matched
        if not matched:
            discrepancies.append({
                "field": "surname",
                "viz_value": viz_surname,
                "mrz_value": mrz_surname,
                "message": f"Surname discrepancy: printed '{viz_surname}' vs MRZ '{mrz_surname}'"
            })

    # 3. Given Names
    viz_given = viz_fields.get("given_names", "").replace(" ", "").upper()
    mrz_given = mrz_data.get("given_names", "").replace(" ", "").upper()
    if viz_given and mrz_given:
        matched = (viz_given in mrz_given or mrz_given in viz_given)
        matches["given_names"] = matched
        if not matched:
            discrepancies.append({
                "field": "given_names",
                "viz_value": viz_given,
                "mrz_value": mrz_given,
                "message": f"Given name discrepancy: printed '{viz_given}' vs MRZ '{mrz_given}'"
            })

    # 4. Nationality
    viz_nat = viz_fields.get("nationality", "").upper()
    mrz_nat = mrz_data.get("nationality", "").upper()
    if viz_nat and mrz_nat:
        matched = (viz_nat == mrz_nat)
        matches["nationality"] = matched
        if not matched:
            discrepancies.append({
                "field": "nationality",
                "viz_value": viz_nat,
                "mrz_value": mrz_nat,
                "message": f"Nationality discrepancy: printed '{viz_nat}' vs MRZ '{mrz_nat}'"
            })

    return {
        "matches": matches,
        "discrepancies": discrepancies,
        "is_consistent": len(discrepancies) == 0
    }
