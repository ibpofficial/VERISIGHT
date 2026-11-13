from dataclasses import dataclass
from typing import Dict, Any, List

ENGINE_VERSION = "VERISIGHT-RULES-v1.2"

@dataclass
class RiskRuleDefinition:
    rule_id: str
    rule_name: str
    category: str  # CRYPTOGRAPHIC | METADATA | FORENSICS | INTEGRITY | QUALITY
    weight: float
    is_critical: bool
    description: str


DEFINED_RULES: Dict[str, RiskRuleDefinition] = {
    "RULE_MRZ_CHECKSUM_FAILURE": RiskRuleDefinition(
        rule_id="RULE_MRZ_CHECKSUM_FAILURE",
        rule_name="ICAO Doc 9303 Check Digit Failure",
        category="CRYPTOGRAPHIC",
        weight=50.0,
        is_critical=True,
        description="One or more weighted 7-3-1 check digits in the MRZ string do not compute correctly."
    ),
    "RULE_VIZ_MRZ_MISMATCH": RiskRuleDefinition(
        rule_id="RULE_VIZ_MRZ_MISMATCH",
        rule_name="Printed Text vs MRZ Discordance",
        category="INTEGRITY",
        weight=40.0,
        is_critical=True,
        description="Printed document number, surname, or date of birth disagrees with encoded MRZ lines."
    ),
    "RULE_MANIPULATION_SOFTWARE_EXIF": RiskRuleDefinition(
        rule_id="RULE_MANIPULATION_SOFTWARE_EXIF",
        rule_name="Digital Editing Software Provenance",
        category="METADATA",
        weight=45.0,
        is_critical=True,
        description="Metadata tags indicate processing via consumer photo manipulation software (Photoshop, Canva, GIMP)."
    ),
    "RULE_DOCUMENT_EXPIRED": RiskRuleDefinition(
        rule_id="RULE_DOCUMENT_EXPIRED",
        rule_name="Travel Credential Expired",
        category="INTEGRITY",
        weight=35.0,
        is_critical=False,
        description="Document validity expiration date has elapsed relative to screening timestamp."
    ),
    "RULE_ELA_SEVERE_DISCONTINUITY": RiskRuleDefinition(
        rule_id="RULE_ELA_SEVERE_DISCONTINUITY",
        rule_name="Error Level Compression Discontinuity",
        category="FORENSICS",
        weight=35.0,
        is_critical=False,
        description="Error Level Analysis identified severe localized residual compression variance clusters."
    ),
    "RULE_PORTRAIT_BOUNDARY_DISCONTINUITY": RiskRuleDefinition(
        rule_id="RULE_PORTRAIT_BOUNDARY_DISCONTINUITY",
        rule_name="Portrait Perimeter Edge Seam",
        category="FORENSICS",
        weight=30.0,
        is_critical=False,
        description="Abrupt perimeter gradient discontinuity detected around document portrait boundaries."
    ),
    "RULE_TEXTURE_IRREGULARITY": RiskRuleDefinition(
        rule_id="RULE_TEXTURE_IRREGULARITY",
        rule_name="Substrate Noise Variance Discordance",
        category="FORENSICS",
        weight=20.0,
        is_critical=False,
        description="Anomalous high-frequency noise variance detected in document surface sectors."
    ),
    "RULE_BASELINE_ALIGNMENT_JITTER": RiskRuleDefinition(
        rule_id="RULE_BASELINE_ALIGNMENT_JITTER",
        rule_name="Typographic Baseline Slant Variance",
        category="FORENSICS",
        weight=15.0,
        is_critical=False,
        description="Printed text lines exhibit irregular angular slant or baseline misalignment."
    ),
    "RULE_LOW_OPTICAL_QUALITY": RiskRuleDefinition(
        rule_id="RULE_LOW_OPTICAL_QUALITY",
        rule_name="Sub-Optimal Acquisition Quality",
        category="QUALITY",
        weight=35.0,
        is_critical=False,
        description="Image exhibits severe specular glare, motion blur, or sub-standard DPI (rescan recommended)."
    ),
    "RULE_OCR_CONFIDENCE_LOW": RiskRuleDefinition(
        rule_id="RULE_OCR_CONFIDENCE_LOW",
        rule_name="Low Optical Character Recognition Confidence",
        category="QUALITY",
        weight=10.0,
        is_critical=False,
        description="Average character extraction confidence fell below evidentiary threshold."
    ),
}
