import pytest
from backend.app.engines.mrz.parser import (
    parse_mrz, parse_mrz_td1, parse_mrz_td2, parse_mrz_td3,
    cross_check_mrz_with_viz, verify_with_auto_correction
)
from backend.app.engines.mrz.check_digits import calculate_mrz_check_digit, verify_check_digit


def test_td3_passport_parsing():
    # Real valid ICAO TD3 passport with 8-char doc number + '<' pad + check digit 9
    line1 = "P<INDVERMA<<VIKRAM<<<<<<<<<<<<<<<<<<<<<<<<<<"
    line2 = "Z9182374<9IND8806150M3006151<<<<<<<<<<<<<<0<"
    mrz = parse_mrz_td3(line1, line2)

    assert mrz["format"] == "TD3"
    assert mrz["surname"] == "VERMA"
    assert mrz["given_names"] == "VIKRAM"
    assert mrz["document_number"] == "Z9182374"
    assert mrz["nationality"] == "IND"
    assert mrz["dob"] == "880615"
    assert mrz["doc_number_check"] is True
    assert mrz["dob_check"] is True
    assert mrz["expiry_check"] is True


def test_td1_identity_card_parsing():
    # 3-line TD1 identity card layout
    # Doc No: D12345678 -> check digit 5
    # DOB: 900815 -> check digit 7
    # Expiry: 300814 -> check digit 4
    line1 = "I<FRAD123456785<<<<<<<<<<<<<<<"
    line2 = "9008157M3008144FRA<<<<<<<<<<<0"
    line3 = "MARTIN<<JEAN<<<<<<<<<<<<<<<<<<"
    mrz = parse_mrz_td1(line1, line2, line3)

    assert mrz["format"] == "TD1"
    assert mrz["surname"] == "MARTIN"
    assert mrz["given_names"] == "JEAN"
    assert mrz["document_number"] == "D12345678"
    assert mrz["issuing_country"] == "FRA"
    assert mrz["dob"] == "900815"
    assert mrz["doc_number_check"] is True
    assert mrz["dob_check"] is True
    assert mrz["expiry_check"] is True


def test_td2_travel_card_parsing():
    # 2-line TD2 official travel credential layout
    line1 = "I<CANMARTIN<<JEAN<<<<<<<<<<<<<<<<<<<"
    line2 = "D123456785CAN9008157M3008144<<<<<<0"
    mrz = parse_mrz_td2(line1, line2)

    assert mrz["format"] == "TD2"
    assert mrz["issuing_country"] == "CAN"
    assert mrz["surname"] == "MARTIN"
    assert mrz["given_names"] == "JEAN"
    assert mrz["document_number"] == "D12345678"
    assert mrz["doc_number_check"] is True
    assert mrz["dob_check"] is True
    assert mrz["expiry_check"] is True


def test_position_aware_ocr_confusion_correction():
    # 'O' (letter O) instead of '0' (digit zero) in DOB
    raw_dob = "9O0815"  # OCR misread 0 as O
    expected_chk = "7"   # Correct 7-3-1 check digit for 900815 is 7
    # verify_check_digit directly fails because 'O' has value 24 instead of 0
    assert verify_check_digit(raw_dob, expected_chk) is False

    # auto-correction fixes 'O' -> '0' and validates check digit
    clean_dob, clean_chk, is_valid, corrs = verify_with_auto_correction(raw_dob, expected_chk, "dob")
    assert is_valid is True
    assert clean_dob == "900815"
    assert len(corrs) > 0
    assert corrs[0]["raw_char"] == "O"
    assert corrs[0]["corrected_char"] == "0"
    assert "OCR-corrected" in corrs[0]["note"]


def test_tampered_mrz_check_digits():
    # Deliberately invalid check digit (expected 7 for 900815, passed 9)
    raw_dob = "900815"
    invalid_chk = "9"
    assert verify_check_digit(raw_dob, invalid_chk) is False

    clean_dob, _, is_valid, _ = verify_with_auto_correction(raw_dob, invalid_chk, "dob")
    assert is_valid is False


def test_cross_check_discrete_states():
    mrz_data = {
        "document_number": "A1234567",
        "surname": "PATEL",
        "given_names": "DEV",
        "nationality": "IND"
    }

    # 1. Exact Match with High Confidence
    viz_fields = {"document_number": "A1234567", "surname": "PATEL", "given_names": "DEV", "nationality": "IND"}
    confidences = {"document_number": 0.95, "surname": 0.92, "given_names": 0.90, "nationality": 0.98}
    res = cross_check_mrz_with_viz(mrz_data, viz_fields, confidences)
    assert res["is_consistent"] is True
    assert res["detailed_status"]["document_number"] == "MATCH"
    assert res["detailed_status"]["surname"] == "MATCH"

    # 2. Definite Mismatch with High Confidence
    viz_tampered = {"document_number": "X9999999", "surname": "PATEL", "given_names": "DEV", "nationality": "IND"}
    res_mismatch = cross_check_mrz_with_viz(mrz_data, viz_tampered, confidences)
    assert res_mismatch["is_consistent"] is False
    assert res_mismatch["detailed_status"]["document_number"] == "MISMATCH"

    # 3. Uncertain due to low OCR confidence (not flagged as MISMATCH!)
    low_confs = {"document_number": 0.40, "surname": 0.92, "given_names": 0.90, "nationality": 0.98}
    res_uncertain = cross_check_mrz_with_viz(mrz_data, viz_tampered, low_confs)
    assert res_uncertain["detailed_status"]["document_number"] == "UNCERTAIN"
    # An uncertain field must NOT create a hard discrepancy
    doc_discrepancies = [d for d in res_uncertain["discrepancies"] if d["field"] == "document_number"]
    assert len(doc_discrepancies) == 0

    # 4. Unavailable when field is missing
    viz_missing = {"surname": "PATEL"}
    res_unavail = cross_check_mrz_with_viz(mrz_data, viz_missing, confidences)
    assert res_unavail["detailed_status"]["document_number"] == "UNAVAILABLE"
