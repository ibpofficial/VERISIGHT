import datetime
from typing import Dict, Any, List, Optional
from backend.app.models import RiskLevel
from backend.app.engines.risk.rules import DEFINED_RULES, ENGINE_VERSION, RiskRuleDefinition


def evaluate_screening_risk(
    quality_record: Optional[Any],
    mrz_record: Optional[Any],
    fields: List[Any],
    forensic_findings: List[Any]
) -> Dict[str, Any]:
    """
    Evaluates document risk using deterministic rules, correlation de-duplication,
    and weighted indicators. Poor quality does not falsely indicate fraud.
    """
    triggered_rules: List[Dict[str, Any]] = []
    has_critical_trigger = False

    is_poor_quality = False
    if quality_record:
        is_poor_quality = getattr(quality_record, "rescan_recommended", False)

    # 1. Check Cryptographic MRZ Check Digits
    if mrz_record:
        doc_chk = getattr(mrz_record, "doc_number_check", True)
        dob_chk = getattr(mrz_record, "dob_check", True)
        exp_chk = getattr(mrz_record, "expiry_check", True)
        comp_chk = getattr(mrz_record, "composite_check", True)

        if not (doc_chk and dob_chk and exp_chk and comp_chk):
            r = DEFINED_RULES["RULE_MRZ_CHECKSUM_FAILURE"]
            triggered_rules.append({
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category,
                "weight": r.weight,
                "is_critical": r.is_critical,
                "description": r.description
            })
            has_critical_trigger = True

        # Cross check printed VIZ vs MRZ
        cross_matches = getattr(mrz_record, "cross_check_matches", {}) or {}
        has_mismatch = any(val is False for val in cross_matches.values())
        if has_mismatch:
            r = DEFINED_RULES["RULE_VIZ_MRZ_MISMATCH"]
            triggered_rules.append({
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category,
                "weight": r.weight,
                "is_critical": r.is_critical,
                "description": r.description
            })
            has_critical_trigger = True

        # Check Expiration date
        exp_str = getattr(mrz_record, "expiry_date", "")
        if len(exp_str) == 6 and exp_str.isdigit():
            # ICAO YYMMDD
            try:
                exp_yy = int(exp_str[0:2])
                exp_mm = int(exp_str[2:4])
                exp_dd = int(exp_str[4:6])
                # Assume 2000s for YY < 70
                full_year = 2000 + exp_yy if exp_yy < 70 else 1900 + exp_yy
                exp_date = datetime.date(full_year, exp_mm, exp_dd)
                if exp_date < datetime.date.today():
                    r = DEFINED_RULES["RULE_DOCUMENT_EXPIRED"]
                    triggered_rules.append({
                        "rule_id": r.rule_id,
                        "rule_name": r.rule_name,
                        "category": r.category,
                        "weight": r.weight,
                        "is_critical": r.is_critical,
                        "description": f"Document expired on {exp_date.isoformat()}."
                    })
            except Exception:
                pass

    # 2. Forensic Findings Rules
    for finding in forensic_findings:
        method = getattr(finding, "analysis_method", None)
        method_str = method.value if hasattr(method, "value") else str(method)
        sev = getattr(finding, "severity", None)
        sev_str = sev.value if hasattr(sev, "value") else str(sev)

        if method_str == "METADATA" and sev_str == "CRITICAL":
            r = DEFINED_RULES["RULE_MANIPULATION_SOFTWARE_EXIF"]
            if not any(tr["rule_id"] == r.rule_id for tr in triggered_rules):
                triggered_rules.append({
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category,
                    "weight": r.weight,
                    "is_critical": r.is_critical,
                    "description": r.description
                })
                has_critical_trigger = True

        elif method_str == "ELA" and sev_str in ["HIGH", "CRITICAL"]:
            r = DEFINED_RULES["RULE_ELA_SEVERE_DISCONTINUITY"]
            if not any(tr["rule_id"] == r.rule_id for tr in triggered_rules):
                triggered_rules.append({
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category,
                    "weight": r.weight,
                    "is_critical": r.is_critical,
                    "description": r.description
                })

        elif method_str == "PORTRAIT" and sev_str in ["HIGH", "CRITICAL"]:
            r = DEFINED_RULES["RULE_PORTRAIT_BOUNDARY_DISCONTINUITY"]
            if not any(tr["rule_id"] == r.rule_id for tr in triggered_rules):
                triggered_rules.append({
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category,
                    "weight": r.weight,
                    "is_critical": r.is_critical,
                    "description": r.description
                })

        elif method_str == "TEXTURE" and sev_str in ["MEDIUM", "HIGH", "CRITICAL"]:
            # Suppress texture alarms if overall image quality is poor (correlation de-duplication)
            if not is_poor_quality:
                r = DEFINED_RULES["RULE_TEXTURE_IRREGULARITY"]
                if not any(tr["rule_id"] == r.rule_id for tr in triggered_rules):
                    triggered_rules.append({
                        "rule_id": r.rule_id,
                        "rule_name": r.rule_name,
                        "category": r.category,
                        "weight": r.weight,
                        "is_critical": r.is_critical,
                        "description": r.description
                    })

        elif method_str == "ALIGNMENT" and sev_str in ["MEDIUM", "HIGH", "CRITICAL"]:
            r = DEFINED_RULES["RULE_BASELINE_ALIGNMENT_JITTER"]
            if not any(tr["rule_id"] == r.rule_id for tr in triggered_rules):
                triggered_rules.append({
                    "rule_id": r.rule_id,
                    "rule_name": r.rule_name,
                    "category": r.category,
                    "weight": r.weight,
                    "is_critical": r.is_critical,
                    "description": r.description
                })

    # 3. Quality Rules
    if is_poor_quality:
        r = DEFINED_RULES["RULE_LOW_OPTICAL_QUALITY"]
        if not any(tr["rule_id"] == r.rule_id for tr in triggered_rules):
            triggered_rules.append({
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category,
                "weight": r.weight,
                "is_critical": r.is_critical,
                "description": r.description
            })
    elif quality_record and getattr(quality_record, "readability_score", 1.0) < 0.70:
        r = DEFINED_RULES["RULE_OCR_CONFIDENCE_LOW"]
        if not any(tr["rule_id"] == r.rule_id for tr in triggered_rules):
            triggered_rules.append({
                "rule_id": r.rule_id,
                "rule_name": r.rule_name,
                "category": r.category,
                "weight": r.weight,
                "is_critical": r.is_critical,
                "description": r.description
            })

    # 4. Compute composite risk score
    raw_score = sum(tr["weight"] for tr in triggered_rules)
    composite_score = min(100.0, max(0.0, float(raw_score)))

    # 5. Deterministic Risk Classification
    if has_critical_trigger or composite_score >= 65.0:
        level = RiskLevel.HIGH_RISK
    elif is_poor_quality or composite_score >= 35.0:
        level = RiskLevel.REVIEW
    else:
        level = RiskLevel.CLEAR

    return {
        "risk_level": level,
        "composite_score": composite_score,
        "engine_version": ENGINE_VERSION,
        "rules_triggered": triggered_rules
    }
