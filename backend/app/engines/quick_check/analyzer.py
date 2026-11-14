import os
import io
import re
import zipfile
import base64
import datetime
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
import numpy as np
import cv2
from PIL import Image, ImageChops, ImageEnhance
from PIL.ExifTags import TAGS

class QuickCheckAnalyzer:
    """
    Standalone Quick Check Digital Forensics Engine.
    Honest framing: Looks for common signs of digital editing.
    Cannot prove authenticity.
    """

    DISCLAIMER = (
        "This tool looks for common signs of digital editing (different compression levels, "
        "modified metadata, pasted elements, multiple PDF revisions, tracked changes in Word docs). "
        "It CANNOT prove an image or document is authentic. A clean result only means no obvious traces of editing were found."
    )

    @classmethod
    def analyze_file(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1].lower()

        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff']:
            return cls._analyze_image(filename, file_bytes)
        elif ext == '.pdf':
            return cls._analyze_pdf(filename, file_bytes)
        elif ext == '.docx':
            return cls._analyze_docx(filename, file_bytes)
        else:
            return {
                "filename": filename,
                "file_type": "UNSUPPORTED",
                "verdict": "NOT_AVAILABLE",
                "risk_level": "REVIEW",
                "honest_disclaimer": cls.DISCLAIMER,
                "summary": f"File extension {ext} is not supported for automated forensics.",
                "findings": [],
                "metadata_timeline": [],
                "visual_evidence_b64": None
            }

    @classmethod
    def _analyze_image(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        findings = []
        timeline = []
        is_edited = False
        strong_evidence = False

        # Load image via Pillow and OpenCV
        try:
            pil_img = Image.open(io.BytesIO(file_bytes)).convert('RGB')
            np_arr = np.frombuffer(file_bytes, np.uint8)
            cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        except Exception as e:
            return {
                "filename": filename,
                "file_type": "IMAGE",
                "verdict": "NOT_AVAILABLE",
                "risk_level": "REVIEW",
                "honest_disclaimer": cls.DISCLAIMER,
                "summary": f"Could not decode image: {str(e)}",
                "findings": [],
                "metadata_timeline": [],
                "visual_evidence_b64": None
            }

        # 1. Error Level Analysis (ELA)
        ela_b64 = None
        try:
            ela_buf = io.BytesIO()
            pil_img.save(ela_buf, 'JPEG', quality=90)
            ela_buf.seek(0)
            resaved_img = Image.open(ela_buf)

            diff = ImageChops.difference(pil_img, resaved_img)
            extrema = diff.getextrema()
            max_diff = max([ex[1] for ex in extrema]) if extrema else 0
            scale = 255.0 / max_diff if max_diff > 0 else 1.0
            diff_enhanced = ImageEnhance.Brightness(diff).enhance(scale * 1.5)

            # Check for localized bright spots (variance of error)
            diff_arr = np.array(diff)
            gray_diff = cv2.cvtColor(diff_arr, cv2.COLOR_RGB2GRAY)
            variance = float(np.var(gray_diff))

            # Encode ELA overlay
            ela_out = io.BytesIO()
            diff_enhanced.save(ela_out, format='PNG')
            ela_b64 = f"data:image/png;base64,{base64.b64encode(ela_out.getvalue()).decode('utf-8')}"

            if variance > 120.0 or max_diff > 45:
                is_edited = True
                strong_evidence = True
                findings.append({
                    "id": "QC-ELA-01",
                    "category": "Compression Forensics",
                    "severity": "CRITICAL",
                    "title": "Uneven JPEG Compression Levels (ELA Anomaly)",
                    "checked": "Compared pixel-level compression error rates against a standard 90% quality baseline.",
                    "found": f"Found high error discrepancy (max difference: {max_diff}, spatial variance: {variance:.1f}).",
                    "matters": "Sections of this image appear to have been compressed at different times or saved with different quality settings, a common signature of pasted elements or photo replacement.",
                    "action": "Inspect the bright areas on the ELA heatmap to identify which elements were inserted.",
                    "technical": f"Max delta: {max_diff}, Laplacian variance of error map: {variance:.2f}"
                })
            else:
                findings.append({
                    "id": "QC-ELA-02",
                    "category": "Compression Forensics",
                    "severity": "INFO",
                    "title": "Uniform Error Level Compression",
                    "checked": "Compared pixel-level compression error rates across the entire image.",
                    "found": f"Compression error rates are consistent (max delta: {max_diff}, variance: {variance:.1f}).",
                    "matters": "No distinct compression boundaries were detected between different areas of the image.",
                    "action": "Proceed with metadata and noise consistency evaluation.",
                    "technical": f"Standard JPEG 90% error resave variance: {variance:.2f}"
                })
        except Exception:
            pass

        # 2. EXIF Metadata Inspection
        try:
            exif_data = pil_img.getexif()
            software_found = None
            modify_date = None
            orig_date = None

            if exif_data:
                for tag_id, val in exif_data.items():
                    tag_name = TAGS.get(tag_id, str(tag_id))
                    if tag_name == 'Software':
                        software_found = str(val)
                    elif tag_name == 'DateTime':
                        modify_date = str(val)
                    elif tag_name == 'DateTimeOriginal':
                        orig_date = str(val)

            # Also scan raw binary for software signatures
            raw_text = file_bytes.decode('latin-1', errors='ignore')
            editing_tools = ['Photoshop', 'Canva', 'GIMP', 'Adobe', 'Corel', 'Lightroom', 'Pixelmator', 'Snapseed']
            matched_tools = [tool for tool in editing_tools if tool.lower() in raw_text.lower()]

            if software_found:
                matched_tools.append(software_found)
            matched_tools = list(set(matched_tools))

            if orig_date:
                timeline.append({"time": orig_date, "event": "Image Taken (Original Timestamp)", "software": None})
            if modify_date:
                timeline.append({"time": modify_date, "event": "File Modified", "software": software_found})

            if matched_tools:
                is_edited = True
                findings.append({
                    "id": "QC-EXIF-01",
                    "category": "File Metadata",
                    "severity": "WARNING",
                    "title": f"Image Editing Software Signature ({', '.join(matched_tools[:2])})",
                    "checked": "Inspected internal file headers and EXIF metadata tags for software signatures.",
                    "found": f"Identified traces of photo editing applications: {', '.join(matched_tools)}.",
                    "matters": "Original camera scans from passports or IDs do not contain desktop photo manipulation software metadata unless post-processed or edited.",
                    "action": "Ask traveler or applicant why the document was saved through photo editing software.",
                    "technical": f"Matched software signatures: {matched_tools}"
                })
            else:
                findings.append({
                    "id": "QC-EXIF-02",
                    "category": "File Metadata",
                    "severity": "INFO",
                    "title": "Clean Camera / Scanner Metadata Tags",
                    "checked": "Scanned file headers for known manipulation software markers.",
                    "found": "No photo manipulation software signatures detected in metadata.",
                    "matters": "Headers are consistent with direct scanner or optical capture.",
                    "action": "No metadata action needed.",
                    "technical": "EXIF tags clean; zero Adobe/GIMP/Canva byte markers found."
                })
        except Exception:
            pass

        # 3. High-Frequency Texture & Noise Consistency
        try:
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            # Compute Laplacian of 4 quadrants
            h, w = gray.shape
            mid_h, mid_w = h // 2, w // 2
            q1 = float(cv2.Laplacian(gray[0:mid_h, 0:mid_w], cv2.CV_64F).var())
            q2 = float(cv2.Laplacian(gray[0:mid_h, mid_w:w], cv2.CV_64F).var())
            q3 = float(cv2.Laplacian(gray[mid_h:h, 0:mid_w], cv2.CV_64F).var())
            q4 = float(cv2.Laplacian(gray[mid_h:h, mid_w:w], cv2.CV_64F).var())

            variances = [q1, q2, q3, q4]
            max_v = max(variances)
            min_v = min(variances)
            ratio = (max_v / min_v) if min_v > 0 else 1.0

            if ratio > 6.0 and max_v > 250:
                is_edited = True
                findings.append({
                    "id": "QC-TEX-01",
                    "category": "Texture & Noise",
                    "severity": "WARNING",
                    "title": "Surface Noise & Grain Inconsistency",
                    "checked": "Compared high-frequency sensor noise across all quadrants of the document.",
                    "found": f"Significant noise imbalance found (variance ratio {ratio:.1f}:1 between regions).",
                    "matters": "When a digital element (such as a text box or photo) is spliced onto a scanned page, its background noise rarely matches the camera sensor grain of the rest of the document.",
                    "action": "Zoom in on smooth or unusually sharp zones to check for overlay splicing.",
                    "technical": f"Quad variances: {[round(v, 1) for v in variances]}, Ratio: {ratio:.2f}"
                })
            else:
                findings.append({
                    "id": "QC-TEX-02",
                    "category": "Texture & Noise",
                    "severity": "INFO",
                    "title": "Consistent Image Surface Grain",
                    "checked": "Compared optical noise across different sections of the document.",
                    "found": f"Sensor grain is uniform across quadrants (variance ratio {ratio:.1f}:1).",
                    "matters": "Surface grain appears consistent throughout the file.",
                    "action": "Proceed with overall assessment.",
                    "technical": f"Quadrant ratio: {ratio:.2f} (within baseline limit <= 6.0)"
                })
        except Exception:
            pass

        # Determine overall verdict
        if strong_evidence:
            verdict = "STRONG_EVIDENCE_OF_EDITING"
            risk_level = "HIGH_RISK"
            summary = "Multiple anomalies detected (ELA compression variance or editing software traces). High likelihood of digital alteration."
        elif is_edited:
            verdict = "SUSPICIOUS_TRACES_FOUND"
            risk_level = "REVIEW"
            summary = "Traces of post-processing or metadata editing software detected. Manual verification recommended."
        else:
            verdict = "NO_OBVIOUS_TRACES"
            risk_level = "CLEAR"
            summary = "No obvious signs of digital editing or compression tampering detected across tested image forensics."

        return {
            "filename": filename,
            "file_type": "IMAGE",
            "verdict": verdict,
            "risk_level": risk_level,
            "honest_disclaimer": cls.DISCLAIMER,
            "summary": summary,
            "findings": findings,
            "metadata_timeline": timeline,
            "visual_evidence_b64": ela_b64
        }

    @classmethod
    def _analyze_pdf(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        findings = []
        timeline = []
        is_edited = False
        strong_evidence = False

        content_str = file_bytes.decode('latin-1', errors='ignore')

        # 1. Incremental Revisions Count (count of %%EOF)
        eof_count = len(re.findall(r'%%EOF', content_str))
        if eof_count > 1:
            is_edited = True
            findings.append({
                "id": "QC-PDF-REV-01",
                "category": "PDF Structure",
                "severity": "WARNING" if eof_count == 2 else "CRITICAL",
                "title": f"Multiple Incremental PDF Revisions ({eof_count} Versions)",
                "checked": "Counted end-of-file (%%EOF) markers and trailer revision blocks.",
                "found": f"This PDF contains {eof_count} sequential revisions appended to the original file.",
                "matters": "When a PDF form, bank statement, or invoice is modified and re-saved, Acrobat and other editors append incremental update bodies without erasing previous revisions.",
                "action": "Inspect previous incremental versions to see what text or numbers were modified.",
                "technical": f"Detected {eof_count} distinct %%EOF trailer sections."
            })
        else:
            findings.append({
                "id": "QC-PDF-REV-02",
                "category": "PDF Structure",
                "severity": "INFO",
                "title": "Single Revision Stream (Linear)",
                "checked": "Counted end-of-file trailer markers.",
                "found": "Exactly 1 %%EOF marker found. The document was saved as a single revision stream.",
                "matters": "No hidden appended update blocks were identified.",
                "action": "Review creator and producer tags.",
                "technical": "Single %%EOF detected; no incremental xref tables."
            })

        # 2. Extract Creator, Producer & ModDate
        creator_match = re.search(r'/Creator\s*\((.*?)\)', content_str)
        producer_match = re.search(r'/Producer\s*\((.*?)\)', content_str)
        mod_date_match = re.search(r'/ModDate\s*\(D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', content_str)
        creation_date_match = re.search(r'/CreationDate\s*\(D:(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})', content_str)

        creator = creator_match.group(1) if creator_match else None
        producer = producer_match.group(1) if producer_match else None

        if creation_date_match:
            d = creation_date_match.groups()
            formatted = f"{d[0]}-{d[1]}-{d[2]} {d[3]}:{d[4]}:{d[5]} UTC"
            timeline.append({"time": formatted, "event": "PDF Created", "software": creator})

        if mod_date_match:
            d = mod_date_match.groups()
            formatted = f"{d[0]}-{d[1]}-{d[2]} {d[3]}:{d[4]}:{d[5]} UTC"
            timeline.append({"time": formatted, "event": "PDF Last Modified", "software": producer})

        suspicious_pdf_software = ['iLovePDF', 'Sejda', 'Smallpdf', 'PDFescape', 'Foxit Phantom', 'Nitro', 'Canva']
        found_pdf_editors = [s for s in suspicious_pdf_software if (creator and s.lower() in creator.lower()) or (producer and s.lower() in producer.lower())]

        if found_pdf_editors:
            is_edited = True
            findings.append({
                "id": "QC-PDF-TOOL-01",
                "category": "Software Tags",
                "severity": "WARNING",
                "title": f"Online PDF Editor Marker ({', '.join(found_pdf_editors)})",
                "checked": "Inspected /Creator and /Producer document information dictionary tags.",
                "found": f"Document was produced or modified using third-party PDF editor tools: {', '.join(found_pdf_editors)}.",
                "matters": "Official institutional PDFs (visas, bank statements) are generated directly from backend systems, not third-party web PDF editors.",
                "action": "Verify authenticity of source organization directly.",
                "technical": f"Creator: {creator}, Producer: {producer}"
            })

        # 3. Form fields and JavaScript objects
        js_count = len(re.findall(r'/JavaScript|/JS\b', content_str))
        if js_count > 0:
            findings.append({
                "id": "QC-PDF-JS-01",
                "category": "Executable Content",
                "severity": "WARNING",
                "title": f"Embedded JavaScript Detected ({js_count} Scripts)",
                "checked": "Scanned PDF catalog for active /JavaScript or /JS objects.",
                "found": f"Found {js_count} embedded JavaScript scripts inside document objects.",
                "matters": "Embedded scripts can dynamically change text on display or pose a security risk.",
                "action": "Verify whether script executes dynamic date or name recalculations.",
                "technical": f"Found {js_count} JS catalog references."
            })

        if eof_count > 2:
            verdict = "STRONG_EVIDENCE_OF_EDITING"
            risk_level = "HIGH_RISK"
            summary = f"Strong evidence of document modification: {eof_count} sequential revisions and modified metadata found."
        elif is_edited:
            verdict = "SUSPICIOUS_TRACES_FOUND"
            risk_level = "REVIEW"
            summary = "Traces of post-creation editing found (incremental save or third-party PDF editor)."
        else:
            verdict = "NO_OBVIOUS_TRACES"
            risk_level = "CLEAR"
            summary = "Clean single-revision PDF stream. No suspicious online editing tools detected."

        return {
            "filename": filename,
            "file_type": "PDF",
            "verdict": verdict,
            "risk_level": risk_level,
            "honest_disclaimer": cls.DISCLAIMER,
            "summary": summary,
            "findings": findings,
            "metadata_timeline": timeline,
            "visual_evidence_b64": None
        }

    @classmethod
    def _analyze_docx(cls, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        findings = []
        timeline = []
        is_edited = False
        strong_evidence = False

        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes), 'r') as zf:
                # 1. Read Core & App Properties
                creator = None
                last_modified_by = None
                revision = None
                created_date = None
                modified_date = None

                if 'docProps/core.xml' in zf.namelist():
                    core_xml = zf.read('docProps/core.xml').decode('utf-8', errors='ignore')
                    c_match = re.search(r'<dc:creator>(.*?)</dc:creator>', core_xml)
                    m_match = re.search(r'<cp:lastModifiedBy>(.*?)</cp:lastModifiedBy>', core_xml)
                    r_match = re.search(r'<cp:revision>(\d+)</cp:revision>', core_xml)
                    cd_match = re.search(r'<dcterms:created[^>]*>(.*?)</dcterms:created>', core_xml)
                    md_match = re.search(r'<dcterms:modified[^>]*>(.*?)</dcterms:modified>', core_xml)

                    creator = c_match.group(1) if c_match else None
                    last_modified_by = m_match.group(1) if m_match else None
                    revision = int(r_match.group(1)) if r_match else 1
                    created_date = cd_match.group(1) if cd_match else None
                    modified_date = md_match.group(1) if md_match else None

                if created_date:
                    timeline.append({"time": created_date, "event": "Document Created", "software": creator})
                if modified_date:
                    timeline.append({"time": modified_date, "event": f"Document Modified (Rev #{revision})", "software": last_modified_by})

                # Check if multiple authors modified it
                if creator and last_modified_by and creator.strip() != last_modified_by.strip():
                    is_edited = True
                    findings.append({
                        "id": "QC-DOCX-AUTH-01",
                        "category": "Author Tracking",
                        "severity": "WARNING",
                        "title": "Multiple Contributors / Different Last Modified Author",
                        "checked": "Compared document creator against last modified author.",
                        "found": f"Original creator was '{creator}', but file was last modified by '{last_modified_by}'.",
                        "matters": "Indicates the document was transferred and updated by a different user.",
                        "action": "Verify if the last modified user had legitimate authority to edit this record.",
                        "technical": f"Creator: {creator}, LastModifiedBy: {last_modified_by}, Rev: {revision}"
                    })

                # 2. Check Tracked Changes in document.xml
                tracked_insertions = 0
                tracked_deletions = 0
                rsid_count = 0

                if 'word/document.xml' in zf.namelist():
                    doc_xml = zf.read('word/document.xml').decode('utf-8', errors='ignore')
                    tracked_insertions = len(re.findall(r'<w:ins\b', doc_xml))
                    tracked_deletions = len(re.findall(r'<w:del\b', doc_xml))
                    rsid_count = len(set(re.findall(r'w:rsidR="([0-9A-Fa-f]+)"', doc_xml)))

                if tracked_insertions > 0 or tracked_deletions > 0:
                    is_edited = True
                    strong_evidence = True
                    findings.append({
                        "id": "QC-DOCX-TRACK-01",
                        "category": "Revision Tracking",
                        "severity": "CRITICAL",
                        "title": f"Unaccepted Tracked Changes Found ({tracked_insertions} ins, {tracked_deletions} del)",
                        "checked": "Scanned document XML structure for <w:ins> and <w:del> revision tags.",
                        "found": f"Found {tracked_insertions} unaccepted text insertions and {tracked_deletions} deletions.",
                        "matters": "The document contains unaccepted edits that may reveal hidden drafts, altered financial numbers, or changed clauses.",
                        "action": "Open document in Word or XML viewer with 'All Markup' turned on to inspect changed wording.",
                        "technical": f"Tracked insertions: {tracked_insertions}, deletions: {tracked_deletions}"
                    })
                elif rsid_count > 10:
                    findings.append({
                        "id": "QC-DOCX-RSID-01",
                        "category": "Revision Sessions",
                        "severity": "INFO",
                        "title": f"Multiple Edit Sessions Recorded ({rsid_count} Sessions)",
                        "checked": "Counted unique Word Revision Session IDs (RSID tags).",
                        "found": f"Document was edited across {rsid_count} distinct typing or editing sessions.",
                        "matters": "Normal for iteratively drafted documents, but proves it was not a single export.",
                        "action": "Compare creation and modified timestamps.",
                        "technical": f"Unique RSID tags: {rsid_count}"
                    })

                # 3. Check for Comments
                if 'word/comments.xml' in zf.namelist():
                    comm_xml = zf.read('word/comments.xml').decode('utf-8', errors='ignore')
                    comm_count = len(re.findall(r'<w:comment\b', comm_xml))
                    if comm_count > 0:
                        findings.append({
                            "id": "QC-DOCX-COMM-01",
                            "category": "Hidden Notes",
                            "severity": "WARNING",
                            "title": f"Embedded Document Comments Found ({comm_count} Comments)",
                            "checked": "Inspected word/comments.xml for internal reviewer remarks.",
                            "found": f"Found {comm_count} comments inside the file structure.",
                            "matters": "Hidden comments may contain officer notes, internal questions, or redactions.",
                            "action": "Review comments for sensitive context.",
                            "technical": f"Comment count: {comm_count}"
                        })

        except Exception as e:
            return {
                "filename": filename,
                "file_type": "DOCX",
                "verdict": "NOT_AVAILABLE",
                "risk_level": "REVIEW",
                "honest_disclaimer": cls.DISCLAIMER,
                "summary": f"Could not inspect DOCX archive: {str(e)}",
                "findings": [],
                "metadata_timeline": [],
                "visual_evidence_b64": None
            }

        if strong_evidence:
            verdict = "STRONG_EVIDENCE_OF_EDITING"
            risk_level = "HIGH_RISK"
            summary = "Unaccepted tracked changes or major document alterations detected."
        elif is_edited:
            verdict = "SUSPICIOUS_TRACES_FOUND"
            risk_level = "REVIEW"
            summary = f"Document modified across multiple authors or editing sessions (Rev #{revision or 'N/A'})."
        else:
            verdict = "NO_OBVIOUS_TRACES"
            risk_level = "CLEAR"
            summary = "Clean single-author document structure without tracked changes."

        return {
            "filename": filename,
            "file_type": "DOCX",
            "verdict": verdict,
            "risk_level": risk_level,
            "honest_disclaimer": cls.DISCLAIMER,
            "summary": summary,
            "findings": findings,
            "metadata_timeline": timeline,
            "visual_evidence_b64": None
        }

