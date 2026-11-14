import cv2
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from backend.app.engines.ocr.base import OCREngine, OCRResultDTO, ExtractedFieldDTO
from backend.app.engines.ocr.field_validator import compute_field_validation_status


class PaddleOCREngine(OCREngine):
    """
    PaddleOCR (PP-OCR) Engine running in CPU mode.
    Extracts high-accuracy text tokens, polygon bounding boxes, and recognition confidences.
    """
    def __init__(self, use_gpu: bool = False):
        self.engine_name = "PaddleOCR"
        self.use_gpu = use_gpu
        self._paddle_instance = None

    def _get_paddle(self):
        if self._paddle_instance is None:
            try:
                from paddleocr import PaddleOCR
                self._paddle_instance = PaddleOCR(
                    use_angle_cls=True,
                    lang='en',
                    use_gpu=self.use_gpu,
                    show_log=False
                )
            except Exception as e:
                self._paddle_instance = False
        return self._paddle_instance

    def extract(self, image_path: str) -> OCRResultDTO:
        start_time = time.time()
        paddle = self._get_paddle()
        if not paddle:
            elapsed_ms = int((time.time() - start_time) * 1000)
            missing_fields = [
                ExtractedFieldDTO(
                    field_name=f,
                    value=None,
                    confidence=None,
                    bounding_box=None,
                    validation_status="MISSING",
                    notes="ENGINE_UNAVAILABLE: PaddleOCR is not installed on host"
                )
                for f in ["document_number", "surname", "given_names", "nationality", "date_of_birth", "expiry_date", "sex"]
            ]
            return OCRResultDTO(
                engine_name=self.engine_name,
                fields=missing_fields,
                raw_mrz_lines=[],
                full_text="",
                execution_time_ms=elapsed_ms,
                status="ENGINE_UNAVAILABLE",
                error_message="paddleocr package is not installed on host"
            )

        img = cv2.imread(image_path)
        if img is None:
            return OCRResultDTO(
                engine_name=self.engine_name,
                fields=[],
                raw_mrz_lines=[],
                full_text="",
                execution_time_ms=0,
                status="EXTRACTION_FAILED",
                error_message=f"Failed to load image at {image_path}"
            )

        h, w = img.shape[:2]
        words: List[Dict[str, Any]] = []
        raw_lines: List[str] = []

        try:
            result = paddle.ocr(img, cls=True)
            if result and result[0]:
                for line in result[0]:
                    pts, (text, conf) = line
                    text_str = str(text).strip()
                    if text_str:
                        raw_lines.append(text_str)
                        min_x = int(min(pt[0] for pt in pts))
                        min_y = int(min(pt[1] for pt in pts))
                        max_x = int(max(pt[0] for pt in pts))
                        max_y = int(max(pt[1] for pt in pts))
                        words.append({
                            "text": text_str,
                            "conf": round(float(conf), 3),
                            "x": min_x,
                            "y": min_y,
                            "w": max_x - min_x,
                            "h": max_y - min_y
                        })
        except Exception as ocr_err:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return OCRResultDTO(
                engine_name=self.engine_name,
                fields=[],
                raw_mrz_lines=[],
                full_text="",
                execution_time_ms=elapsed_ms,
                status="EXTRACTION_FAILED",
                error_message=f"PaddleOCR inference failed: {str(ocr_err)}"
            )

        full_raw_text = "\n".join(raw_lines)

        # Real MRZ line detection
        mrz_lines: List[str] = []
        for line in raw_lines:
            cleaned = line.replace(' ', '').upper()
            if '<' in cleaned and len(cleaned) >= 28:
                mrz_lines.append(cleaned)

        def get_word_evidence(target_tokens: List[str]) -> Tuple[Optional[Dict[str, int]], Optional[float]]:
            if not target_tokens:
                return None, None
            matched = []
            for token in target_tokens:
                token_clean = re.sub(r'[^A-Z0-9]', '', token.upper())
                if not token_clean:
                    continue
                for w_info in words:
                    w_clean = re.sub(r'[^A-Z0-9]', '', w_info["text"].upper())
                    if token_clean in w_clean or w_clean in token_clean:
                        matched.append(w_info)
            if not matched:
                return None, None
            min_x = min(m["x"] for m in matched)
            min_y = min(m["y"] for m in matched)
            max_x = max(m["x"] + m["w"] for m in matched)
            max_y = max(m["y"] + m["h"] for m in matched)
            bbox = {"x": min_x, "y": min_y, "w": max_x - min_x, "h": max_y - min_y}
            mean_conf = round(sum(m["conf"] for m in matched) / len(matched), 2)
            return bbox, mean_conf

        def extract_anchored_field(
            label_patterns: List[str],
            value_pattern: Optional[str] = None
        ) -> Tuple[Optional[str], Optional[Dict[str, int]], Optional[float]]:
            for i, line in enumerate(raw_lines):
                line_upper = line.upper()
                for pat in label_patterns:
                    if re.search(r'\b' + pat + r'\b', line_upper):
                        sub = line_upper.split(pat, 1)[-1].strip(': -')
                        if sub:
                            if value_pattern:
                                m = re.search(value_pattern, sub)
                                if m:
                                    val = m.group(0).strip()
                                    bbox, conf = get_word_evidence(val.split())
                                    return val, bbox, conf
                            elif len(sub) > 1:
                                val = sub.split('\n')[0].strip()
                                bbox, conf = get_word_evidence(val.split())
                                return val, bbox, conf
                        if i + 1 < len(raw_lines):
                            next_line = raw_lines[i + 1].strip()
                            if value_pattern:
                                m = re.search(value_pattern, next_line.upper())
                                if m:
                                    val = m.group(0).strip()
                                    bbox, conf = get_word_evidence(val.split())
                                    return val, bbox, conf
                            elif next_line and not any(p in next_line.upper() for p in label_patterns):
                                val = next_line
                                bbox, conf = get_word_evidence(val.split())
                                return val, bbox, conf
            return None, None, None

        fields: List[ExtractedFieldDTO] = []

        # 1. Document Number
        doc_val, doc_box, doc_conf = extract_anchored_field(
            ["PASSPORT NO", "PASSPORT NUMBER", "DOC NO", "DOCUMENT NO", "NO DE PASSEPORT", "PASSPORT"],
            r'[A-Z0-9]{7,10}'
        )
        if not doc_val:
            m = re.search(r'\b([A-Z][0-9]{7,8}|[0-9]{8,9})\b', full_raw_text)
            if m:
                doc_val = m.group(1)
                doc_box, doc_conf = get_word_evidence([doc_val])

        status = compute_field_validation_status("document_number", doc_val, doc_conf)
        fields.append(ExtractedFieldDTO(
            field_name="document_number",
            value=doc_val,
            confidence=doc_conf,
            bounding_box=doc_box,
            validation_status=status.value
        ))

        # 2. Surname
        sur_val, sur_box, sur_conf = extract_anchored_field(
            ["SURNAME", "NOM", "LAST NAME", "उपपनाम", "FAMILY NAME"]
        )
        if sur_val:
            sur_val = re.sub(r'[^A-Z\s\-]', '', sur_val.upper()).strip()
        status = compute_field_validation_status("surname", sur_val, sur_conf)
        fields.append(ExtractedFieldDTO(
            field_name="surname",
            value=sur_val,
            confidence=sur_conf,
            bounding_box=sur_box,
            validation_status=status.value
        ))

        # 3. Given Names
        giv_val, giv_box, giv_conf = extract_anchored_field(
            ["GIVEN NAMES", "GIVEN NAME", "PRENOMS", "FIRST NAME", "नाम"]
        )
        if giv_val:
            giv_val = re.sub(r'[^A-Z\s\-]', '', giv_val.upper()).strip()
        status = compute_field_validation_status("given_names", giv_val, giv_conf)
        fields.append(ExtractedFieldDTO(
            field_name="given_names",
            value=giv_val,
            confidence=giv_conf,
            bounding_box=giv_box,
            validation_status=status.value
        ))

        # 4. Nationality
        nat_val, nat_box, nat_conf = extract_anchored_field(
            ["NATIONALITY", "NATIONALITÉ", "CITIZENSHIP", "राष्ट्रीयता"],
            r'[A-Z]{3}'
        )
        if not nat_val:
            m = re.search(r'\b(IND|GBR|USA|FRA|CAN|DEU|AUS|JPN|SGP|NZL)\b', full_raw_text.upper())
            if m:
                nat_val = m.group(1)
                nat_box, nat_conf = get_word_evidence([nat_val])
        status = compute_field_validation_status("nationality", nat_val, nat_conf)
        fields.append(ExtractedFieldDTO(
            field_name="nationality",
            value=nat_val,
            confidence=nat_conf,
            bounding_box=nat_box,
            validation_status=status.value
        ))

        # 5. DOB and Expiry
        date_pattern = r'(\d{2}[/\-\.]\d{2}[/\-\.]\d{4}|\d{2}\s+[A-Z]{3}\s+\d{4})'
        dob_val, dob_box, dob_conf = extract_anchored_field(
            ["DATE OF BIRTH", "DOB", "DATE DE NAISSANCE", "BIRTH DATE", "DOB/"],
            date_pattern
        )
        status = compute_field_validation_status("date_of_birth", dob_val, dob_conf)
        fields.append(ExtractedFieldDTO(
            field_name="date_of_birth",
            value=dob_val,
            confidence=dob_conf,
            bounding_box=dob_box,
            validation_status=status.value
        ))

        exp_val, exp_box, exp_conf = extract_anchored_field(
            ["DATE OF EXPIRY", "EXPIRY DATE", "EXPIRY", "EXPIRATION", "DATE D'EXPIRATION", "VALID UNTIL"],
            date_pattern
        )
        status = compute_field_validation_status("expiry_date", exp_val, exp_conf)
        fields.append(ExtractedFieldDTO(
            field_name="expiry_date",
            value=exp_val,
            confidence=exp_conf,
            bounding_box=exp_box,
            validation_status=status.value
        ))

        # 6. Sex
        sex_val, sex_box, sex_conf = extract_anchored_field(
            ["SEX", "SEXE", "GENDER", "लिंग"],
            r'\b[MFX]\b'
        )
        status = compute_field_validation_status("sex", sex_val, sex_conf)
        fields.append(ExtractedFieldDTO(
            field_name="sex",
            value=sex_val,
            confidence=sex_conf,
            bounding_box=sex_box,
            validation_status=status.value
        ))

        elapsed_ms = int((time.time() - start_time) * 1000)
        return OCRResultDTO(
            engine_name=self.engine_name,
            fields=fields,
            raw_mrz_lines=mrz_lines,
            full_text=full_raw_text,
            execution_time_ms=elapsed_ms,
            status="SUCCESS"
        )
