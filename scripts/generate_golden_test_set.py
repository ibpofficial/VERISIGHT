import os
import json
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures")
os.makedirs(FIXTURES_DIR, exist_ok=True)

# ICAO Doc 9303 Modulo-10 Check Digit Calculator
def calc_check_digit(chars: str) -> str:
    weights = [7, 3, 1]
    total = 0
    for i, c in enumerate(chars):
        if '0' <= c <= '9':
            val = int(c)
        elif 'A' <= c <= 'Z':
            val = ord(c) - ord('A') + 10
        elif c == '<':
            val = 0
        else:
            val = 0
        total += val * weights[i % 3]
    return str(total % 10)

def draw_passport_base(surname, given_names, doc_num, nat, dob_yymmdd, expiry_yymmdd, sex="M", is_valid_mrz=True):
    # Standard 1000x700 canvas for TD3 passport
    img = np.ones((700, 1000, 3), dtype=np.uint8) * 238 # Paper off-white background
    
    # Border Guilloche simulation lines
    for y in range(20, 680, 40):
        cv2.line(img, (20, y), (980, y), (220, 225, 230), 1)

    # Document Header
    cv2.putText(img, f"PASSPORT / PASSEPORT", (320, 50), cv2.FONT_HERSHEY_DUPLEX, 1.0, (20, 30, 60), 2)
    cv2.putText(img, f"REPUBLIC OF {nat}", (320, 85), cv2.FONT_HERSHEY_DUPLEX, 0.7, (60, 70, 90), 1)
    
    # Emblem / Shield Placeholder
    cv2.circle(img, (260, 65), 30, (180, 150, 50), 2)
    cv2.putText(img, nat[:3], (245, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 150, 50), 2)

    # Photo Box (Left)
    cv2.rectangle(img, (50, 120), (280, 420), (190, 190, 190), -1)
    cv2.rectangle(img, (50, 120), (280, 420), (80, 80, 80), 2)
    # Draw simple facial avatar inside photo box
    cv2.circle(img, (165, 230), 55, (120, 120, 120), -1) # Head
    cv2.ellipse(img, (165, 360), (80, 90), 0, 0, 180, (90, 90, 90), -1) # Shoulders
    cv2.putText(img, "PORTRAIT", (125, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Visual Inspection Zone (VIZ) Fields
    y_start = 140
    fields = [
        ("Type / Type", "P"),
        ("Country Code / Pays", nat),
        ("Passport No. / No. du Passeport", doc_num),
        ("Surname / Nom", surname),
        ("Given Names / Prenoms", given_names),
        ("Nationality / Nationalite", nat),
        ("Date of Birth / Date de naissance", f"{dob_yymmdd[4:6]}/{dob_yymmdd[2:4]}/19{dob_yymmdd[0:2]}"),
        ("Sex / Sexe", sex),
        ("Date of Expiry / Date d'expiration", f"{expiry_yymmdd[4:6]}/{expiry_yymmdd[2:4]}/20{expiry_yymmdd[0:2]}"),
    ]

    for label, val in fields:
        cv2.putText(img, label, (320, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 105, 115), 1)
        cv2.putText(img, val, (320, y_start + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (15, 20, 30), 2)
        y_start += 36

    # Machine Readable Zone (MRZ TD3: 2 lines x 44 characters)
    # Line 1: P<NAT SURNAME<<GIVEN<NAMES<<<<<<<<<<<<<<<<<<
    name_field = f"{surname.upper()}<<{given_names.upper()}".replace(" ", "<")
    line1 = f"P<{nat}{name_field}"
    line1 = line1[:44].ljust(44, "<")

    # Line 2: DOCNUM + CHECK + NAT + DOB + CHECK + SEX + EXP + CHECK + OPT + COMPOSITE_CHECK
    cd_doc = calc_check_digit(doc_num) if is_valid_mrz else ("0" if calc_check_digit(doc_num) != "0" else "9")
    cd_dob = calc_check_digit(dob_yymmdd)
    cd_exp = calc_check_digit(expiry_yymmdd)
    optional_data = "".ljust(14, "<")
    
    composite_raw = doc_num + cd_doc + dob_yymmdd + cd_dob + expiry_yymmdd + cd_exp + optional_data
    cd_comp = calc_check_digit(composite_raw)

    line2 = f"{doc_num}{cd_doc}{nat}{dob_yymmdd}{cd_dob}{sex}{expiry_yymmdd}{cd_exp}{optional_data}{cd_comp}"
    line2 = line2[:44].ljust(44, "<")

    # MRZ Background Band
    cv2.rectangle(img, (30, 520), (970, 670), (245, 248, 250), -1)
    cv2.rectangle(img, (30, 520), (970, 670), (180, 190, 200), 1)

    # Monospace OCR-B simulated rendering
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, line1, (45, 575), font, 0.72, (10, 10, 10), 2)
    cv2.putText(img, line2, (45, 635), font, 0.72, (10, 10, 10), 2)

    return img, {
        "document_type": "PASSPORT_TD3",
        "surname": surname,
        "given_names": given_names,
        "document_number": doc_num,
        "nationality": nat,
        "dob": dob_yymmdd,
        "expiry_date": expiry_yymmdd,
        "sex": sex,
        "mrz_line1": line1,
        "mrz_line2": line2,
        "is_valid_mrz": is_valid_mrz
    }

print("Generating 35 Synthetic Golden Test Fixtures...")
generated_count = 0
manifest = []

def save_fixture(filename, img, metadata, ground_truth):
    filepath = os.path.join(FIXTURES_DIR, filename)
    json_path = os.path.splitext(filepath)[0] + ".json"
    
    if img is not None:
        cv2.imwrite(filepath, img)
    
    meta_record = {
        "filename": filename,
        "condition": metadata.get("condition", "STANDARD"),
        "expected_extractable": metadata.get("expected_extractable", True),
        "expected_risk": metadata.get("expected_risk", "CLEAR"),
        "notes": metadata.get("notes", ""),
        "ground_truth": ground_truth
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(meta_record, f, indent=2)
    
    manifest.append(meta_record)

# 1-3. Clean Valid TD3 Passports
for nat, sname, gname, dnum in [
    ("IND", "VERMA", "VIKRAM", "Z9182374"),
    ("GBR", "BLACKWOOD", "ELEANOR", "948210384"),
    ("USA", "VANCE", "MARCUS", "C08429184")
]:
    generated_count += 1
    fname = f"sample_{generated_count:02d}_clean_td3_{nat.lower()}.jpg"
    img, gt = draw_passport_base(sname, gname, dnum, nat, "880615", "300615")
    save_fixture(fname, img, {"condition": "CLEAN", "expected_risk": "CLEAR", "notes": f"Clean valid {nat} passport"}, gt)

# 4. Clean TD1 ID Card (3 lines x 30 chars)
generated_count += 1
img_td1 = np.ones((500, 800, 3), dtype=np.uint8) * 240
cv2.putText(img_td1, "NATIONAL IDENTITY CARD", (220, 50), cv2.FONT_HERSHEY_DUPLEX, 0.7, (20, 20, 40), 2)
cv2.putText(img_td1, "Surname: DUBOIS", (240, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
cv2.putText(img_td1, "Name: CLAIRE", (240, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
cv2.putText(img_td1, "Doc No: 180948201", (240, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
# TD1 3 lines
l1 = "I<FRA1809482015<<<<<<<<<<<<<<<"
l2 = "9204128F3108154FRA<<<<<<<<<<<8"
l3 = "DUBOIS<<CLAIRE<<<<<<<<<<<<<<<<"
cv2.putText(img_td1, l1, (40, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2)
cv2.putText(img_td1, l2, (40, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2)
cv2.putText(img_td1, l3, (40, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2)
save_fixture(f"sample_{generated_count:02d}_clean_td1_fra.jpg", img_td1, {"condition": "CLEAN_TD1", "expected_risk": "CLEAR"}, {
    "document_type": "ID_TD1", "surname": "DUBOIS", "given_names": "CLAIRE", "document_number": "180948201"
})

# 5. Clean TD2 Visa (2 lines x 36 chars)
generated_count += 1
img_td2 = np.ones((550, 850, 3), dtype=np.uint8) * 235
cv2.putText(img_td2, "CANADA VISA / VISA", (260, 60), cv2.FONT_HERSHEY_DUPLEX, 0.8, (20, 30, 60), 2)
cv2.putText(img_td2, "Surname: KOWALSKI", (260, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
cv2.putText(img_td2, "Given: JAN", (260, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
l1 = "V<CANKOWALSKI<<JAN<<<<<<<<<<<<<<<<<<"
l2 = "E918237414CAN8401123M2801124<<<<<<<<<"
cv2.putText(img_td2, l1, (40, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2)
cv2.putText(img_td2, l2, (40, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 0, 0), 2)
save_fixture(f"sample_{generated_count:02d}_clean_td2_can.jpg", img_td2, {"condition": "CLEAN_TD2", "expected_risk": "CLEAR"}, {
    "document_type": "VISA_TD2", "surname": "KOWALSKI", "given_names": "JAN", "document_number": "E91823741"
})

# 6-8. Rotations (90, 180, 270)
base_img, base_gt = draw_passport_base("MEHTA", "ANANYA", "K4918204", "IND", "950820", "350820")
for deg, code in [(90, cv2.ROTATE_90_CLOCKWISE), (180, cv2.ROTATE_180), (270, cv2.ROTATE_90_COUNTERCLOCKWISE)]:
    generated_count += 1
    rot_img = cv2.rotate(base_img, code)
    save_fixture(f"sample_{generated_count:02d}_rotated_{deg}deg.jpg", rot_img, {"condition": f"ROTATED_{deg}", "expected_risk": "CLEAR"}, base_gt)

# 9-10. Skews (5 deg, 15 deg)
for deg in [5, 15]:
    generated_count += 1
    h, w = base_img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), deg, 1.0)
    skewed = cv2.warpAffine(base_img, M, (w, h), borderValue=(255, 255, 255))
    save_fixture(f"sample_{generated_count:02d}_skewed_{deg}deg.jpg", skewed, {"condition": f"SKEWED_{deg}DEG", "expected_risk": "CLEAR"}, base_gt)

# 11. Perspective Photographed
generated_count += 1
h, w = base_img.shape[:2]
pts1 = np.float32([[0,0], [w,0], [0,h], [w,h]])
pts2 = np.float32([[40, 60], [w-60, 20], [80, h-40], [w-20, h-10]])
M_persp = cv2.getPerspectiveTransform(pts1, pts2)
persp_img = cv2.warpPerspective(base_img, M_persp, (w, h), borderValue=(210, 210, 210))
save_fixture(f"sample_{generated_count:02d}_perspective_trapezoid.jpg", persp_img, {"condition": "PERSPECTIVE", "expected_risk": "CLEAR"}, base_gt)

# 12. Low light / underexposed
generated_count += 1
dark_img = (base_img * 0.22).astype(np.uint8)
save_fixture(f"sample_{generated_count:02d}_low_light.jpg", dark_img, {"condition": "LOW_LIGHT", "expected_risk": "REVIEW"}, base_gt)

# 13. Specular glare flash
generated_count += 1
glare_img = base_img.copy()
cv2.circle(glare_img, (450, 300), 130, (255, 255, 255), -1)
glare_img = cv2.GaussianBlur(glare_img, (15, 15), 0)
save_fixture(f"sample_{generated_count:02d}_specular_glare.jpg", glare_img, {"condition": "GLARE", "expected_risk": "REVIEW"}, base_gt)

# 14. Severe Gaussian blur
generated_count += 1
blur_img = cv2.GaussianBlur(base_img, (35, 35), 0)
save_fixture(f"sample_{generated_count:02d}_gaussian_blur.jpg", blur_img, {"condition": "BLURRED", "expected_risk": "REVIEW"}, base_gt)

# 15. Motion blur
generated_count += 1
size = 25
kernel_motion = np.zeros((size, size))
kernel_motion[int((size-1)/2), :] = np.ones(size)
kernel_motion = kernel_motion / size
motion_img = cv2.filter2D(base_img, -1, kernel_motion)
save_fixture(f"sample_{generated_count:02d}_motion_blur.jpg", motion_img, {"condition": "MOTION_BLUR", "expected_risk": "REVIEW"}, base_gt)

# 16. Cropped (Bottom MRZ missing)
generated_count += 1
cropped_mrz = base_img[:480, :].copy()
save_fixture(f"sample_{generated_count:02d}_cropped_missing_mrz.jpg", cropped_mrz, {"condition": "CROPPED_MRZ", "expected_risk": "REVIEW"}, base_gt)

# 17. Cropped Corners
generated_count += 1
corner_crop = base_img[60:640, 80:920].copy()
save_fixture(f"sample_{generated_count:02d}_corner_crop.jpg", corner_crop, {"condition": "CORNER_CROP", "expected_risk": "REVIEW"}, base_gt)

# 18. Heavy JPEG compression Q=20
generated_count += 1
_, enc = cv2.imencode(".jpg", base_img, [int(cv2.IMWRITE_JPEG_QUALITY), 20])
q20_img = cv2.imdecode(enc, cv2.IMREAD_COLOR)
save_fixture(f"sample_{generated_count:02d}_jpeg_recompressed_q20.jpg", q20_img, {"condition": "HEAVY_JPEG", "expected_risk": "REVIEW"}, base_gt)

# 19. Multi-cycle resize
generated_count += 1
small = cv2.resize(base_img, (300, 210))
multicycle = cv2.resize(small, (1000, 700), interpolation=cv2.INTER_NEAREST)
save_fixture(f"sample_{generated_count:02d}_multicycle_resize.jpg", multicycle, {"condition": "MULTICYCLE_RESIZE", "expected_risk": "REVIEW"}, base_gt)

# 20. Desktop Screenshot
generated_count += 1
screenshot = np.ones((900, 1400, 3), dtype=np.uint8) * 60 # Dark wallpaper
scaled_base = cv2.resize(base_img, (800, 560))
screenshot[150:710, 300:1100] = scaled_base
save_fixture(f"sample_{generated_count:02d}_desktop_screenshot.png", screenshot, {"condition": "SCREENSHOT", "expected_risk": "REVIEW"}, base_gt)

# 21-22. Non-MRZ Identity Cards
generated_count += 1
dl_img = np.ones((500, 800, 3), dtype=np.uint8) * 240
cv2.putText(dl_img, "DRIVING LICENCE", (240, 60), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 100), 2)
cv2.putText(dl_img, "Name: RAJESH PATEL", (240, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
cv2.putText(dl_img, "Licence No: DL-1420110029", (240, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(dl_img, "DOB: 12/08/1985", (240, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
save_fixture(f"sample_{generated_count:02d}_non_mrz_driving_license.jpg", dl_img, {"condition": "NON_MRZ_DL", "expected_risk": "REVIEW"}, {
    "document_type": "DOMESTIC_ID", "surname": "PATEL", "given_names": "RAJESH", "document_number": "DL-1420110029"
})

generated_count += 1
badge_img = np.ones((600, 450, 3), dtype=np.uint8) * 250
cv2.putText(badge_img, "EMPLOYEE PASS", (120, 60), cv2.FONT_HERSHEY_DUPLEX, 0.7, (30, 30, 30), 2)
cv2.circle(badge_img, (225, 200), 70, (180, 180, 180), -1)
cv2.putText(badge_img, "ID: EMP-8819", (150, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
cv2.putText(badge_img, "NAME: SARAH CONNER", (100, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0), 2)
save_fixture(f"sample_{generated_count:02d}_non_mrz_badge.jpg", badge_img, {"condition": "NON_MRZ_BADGE", "expected_risk": "REVIEW"}, {
    "document_type": "BADGE", "surname": "CONNER", "given_names": "SARAH", "document_number": "EMP-8819"
})

# 23-24. Random Non-Document Photos
generated_count += 1
nature_img = np.zeros((600, 800, 3), dtype=np.uint8)
nature_img[:300, :] = [240, 180, 100] # Sky
nature_img[300:, :] = [40, 140, 30]   # Grass
cv2.circle(nature_img, (650, 150), 60, [0, 240, 255], -1) # Sun
save_fixture(f"sample_{generated_count:02d}_random_photo_nature.jpg", nature_img, {"condition": "NON_DOCUMENT", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

generated_count += 1
pattern_img = np.zeros((600, 800, 3), dtype=np.uint8)
for i in range(0, 800, 40):
    cv2.line(pattern_img, (i, 0), (800-i, 600), (i%255, (i*2)%255, 200), 2)
save_fixture(f"sample_{generated_count:02d}_random_photo_abstract.jpg", pattern_img, {"condition": "NON_DOCUMENT", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

# 25-27. Pure Blank Images
generated_count += 1
white_img = np.ones((600, 800, 3), dtype=np.uint8) * 255
save_fixture(f"sample_{generated_count:02d}_blank_white.png", white_img, {"condition": "BLANK_WHITE", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

generated_count += 1
black_img = np.zeros((600, 800, 3), dtype=np.uint8)
save_fixture(f"sample_{generated_count:02d}_blank_black.png", black_img, {"condition": "BLANK_BLACK", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

generated_count += 1
noise_img = np.random.normal(128, 40, (600, 800, 3)).clip(0, 255).astype(np.uint8)
save_fixture(f"sample_{generated_count:02d}_blank_noise.png", noise_img, {"condition": "BLANK_NOISE", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

# 28-29. Text-only Pages (Article / Code snippet)
generated_count += 1
code_img = np.ones((700, 900, 3), dtype=np.uint8) * 255
code_lines = [
    "def calculate_quantum_entropy(matrix: np.ndarray) -> float:",
    "    # Standard thermodynamic entropy computation",
    "    eigenvalues = np.linalg.eigvalsh(matrix)",
    "    probabilities = np.exp(eigenvalues) / np.sum(np.exp(eigenvalues))",
    "    return -np.sum(probabilities * np.log2(probabilities + 1e-12))",
    "",
    "if __name__ == '__main__':",
    "    test_mat = np.random.randn(10, 10)",
    "    print('Entropy:', calculate_quantum_entropy(test_mat))"
]
for idx, line in enumerate(code_lines):
    cv2.putText(code_img, line, (50, 80 + idx * 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2)
save_fixture(f"sample_{generated_count:02d}_text_only_code.png", code_img, {"condition": "TEXT_ONLY_CODE", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

generated_count += 1
article_img = np.ones((700, 900, 3), dtype=np.uint8) * 255
prose_lines = [
    "THE FUTURE OF AUTONOMOUS SYSTEMS IN MARITIME COMMERCE",
    "Recent advances in container tracking and satellite telemetry have enabled",
    "freight operators to dynamically optimize fuel burn across international sea lanes.",
    "However, physical inspections of customs manifests and shipping containers remain",
    "a manual bottleneck at major transshipment hubs throughout Southeast Asia."
]
for idx, line in enumerate(prose_lines):
    cv2.putText(article_img, line, (50, 100 + idx * 50), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (20, 20, 20), 2)
save_fixture(f"sample_{generated_count:02d}_text_only_article.jpg", article_img, {"condition": "TEXT_ONLY_PROSE", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

# 30. Invalid DOB Check Digit (Deliberate Counterfeit)
generated_count += 1
invalid_dob_img, gt_idob = draw_passport_base("KAPOOR", "ROHAN", "T8192038", "IND", "901122", "301122")
# Tamper DOB in Line 2: change birth year from 90 to 80 without updating check digit
parts = list(gt_idob["mrz_line2"])
parts[13] = "8" # was 9
tampered_l2 = "".join(parts)
# Re-render bottom line
cv2.rectangle(invalid_dob_img, (35, 610), (965, 660), (245, 248, 250), -1)
cv2.putText(invalid_dob_img, tampered_l2, (45, 635), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (10, 10, 10), 2)
gt_idob["mrz_line2"] = tampered_l2
gt_idob["is_valid_mrz"] = False
save_fixture(f"sample_{generated_count:02d}_tampered_dob_checksum_td3.jpg", invalid_dob_img, {"condition": "INVALID_DOB_CHECKSUM", "expected_risk": "HIGH_RISK", "notes": "DOB check digit deliberately failed"}, gt_idob)

# 31. Invalid Document Number Check Digit
generated_count += 1
invalid_doc_img, gt_idoc = draw_passport_base("SINGH", "HARPREET", "Z1092834", "IND", "860314", "260314")
parts = list(gt_idoc["mrz_line2"])
# Change check digit at index 9 from correct to invalid
cur_cd = parts[9]
parts[9] = "9" if cur_cd != "9" else "0"
tampered_l2 = "".join(parts)
cv2.rectangle(invalid_doc_img, (35, 610), (965, 660), (245, 248, 250), -1)
cv2.putText(invalid_doc_img, tampered_l2, (45, 635), cv2.FONT_HERSHEY_SIMPLEX, 0.72, (10, 10, 10), 2)
gt_idoc["mrz_line2"] = tampered_l2
gt_idoc["is_valid_mrz"] = False
save_fixture(f"sample_{generated_count:02d}_tampered_docnum_checksum_td3.jpg", invalid_doc_img, {"condition": "INVALID_DOCNUM_CHECKSUM", "expected_risk": "HIGH_RISK"}, gt_idoc)

# 32. Spliced Altered Photo Box
generated_count += 1
spliced_img = base_img.copy()
# Paste high-frequency random noise inside portrait
noise_patch = np.random.randint(40, 220, (300, 230, 3), dtype=np.uint8)
spliced_img[120:420, 50:280] = noise_patch
save_fixture(f"sample_{generated_count:02d}_spliced_portrait_tampered_td3.jpg", spliced_img, {"condition": "SPLICED_PORTRAIT", "expected_risk": "HIGH_RISK"}, base_gt)

# 33. Truncated / Corrupt JPEG File
generated_count += 1
_, valid_bytes = cv2.imencode(".jpg", base_img)
corrupt_bytes = valid_bytes.tobytes()[: len(valid_bytes) // 4] # Truncate 75%
corrupt_path = os.path.join(FIXTURES_DIR, f"sample_{generated_count:02d}_corrupted_truncated.jpg")
with open(corrupt_path, "wb") as f:
    f.write(corrupt_bytes)
save_fixture(f"sample_{generated_count:02d}_corrupted_truncated.jpg", None, {"condition": "CORRUPTED_FILE", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

# 34. Zero-byte empty file
generated_count += 1
empty_path = os.path.join(FIXTURES_DIR, f"sample_{generated_count:02d}_empty_0bytes.jpg")
with open(empty_path, "wb") as f:
    pass
save_fixture(f"sample_{generated_count:02d}_empty_0bytes.jpg", None, {"condition": "ZERO_BYTES", "expected_extractable": False, "expected_risk": "REVIEW"}, {})

# 35. Text and Photo Disconnected Multi-Mismatch
generated_count += 1
mismatch_img, gt_mismatch = draw_passport_base("REDDY", "KAVITHA", "R9910283", "IND", "941010", "341010")
# Swap printed VIZ name to different identity
cv2.rectangle(mismatch_img, (315, 235), (700, 275), (238, 238, 238), -1)
cv2.putText(mismatch_img, "JOSHI", (320, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (15, 20, 30), 2)
gt_mismatch["surname"] = "JOSHI"
save_fixture(f"sample_{generated_count:02d}_mismatch_viz_vs_mrz_td3.jpg", mismatch_img, {"condition": "VIZ_MRZ_MISMATCH", "expected_risk": "HIGH_RISK"}, gt_mismatch)

# Save Master Manifest
manifest_path = os.path.join(FIXTURES_DIR, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print(f"Successfully generated {generated_count} synthetic golden fixtures in {FIXTURES_DIR} with master manifest.json!")
