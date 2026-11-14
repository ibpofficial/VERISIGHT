import io
import zipfile
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.engines.quick_check.analyzer import QuickCheckAnalyzer

client = TestClient(app)

def test_quick_check_analyzer_image():
    # Generate clean in-memory JPEG
    img = Image.new('RGB', (200, 200), color=(200, 200, 200))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    buf.seek(0)
    img_bytes = buf.getvalue()

    result = QuickCheckAnalyzer.analyze_file("passport_test.jpg", img_bytes)
    assert result["file_type"] == "IMAGE"
    assert "verdict" in result
    assert "honest_disclaimer" in result
    assert isinstance(result["findings"], list)
    assert len(result["findings"]) > 0

def test_quick_check_analyzer_pdf_incremental():
    # PDF with multiple %%EOF markers
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Title (Original) >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R >>\n%%EOF\n"
        b"2 0 obj\n<< /Title (Modified) >>\nendobj\n"
        b"trailer\n<< /Root 2 0 R >>\n%%EOF\n"
    )
    result = QuickCheckAnalyzer.analyze_file("statement.pdf", pdf_bytes)
    assert result["file_type"] == "PDF"
    assert result["verdict"] in ["SUSPICIOUS_TRACES_FOUND", "STRONG_EVIDENCE_OF_EDITING"]
    # Should identify multiple revisions
    rev_findings = [f for f in result["findings"] if "Revisions" in f["title"]]
    assert len(rev_findings) > 0

def test_quick_check_analyzer_docx_tracked_changes():
    # In-memory DOCX zip archive with tracked changes
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('docProps/core.xml', '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:creator>Original Author</dc:creator><cp:lastModifiedBy>Editor</cp:lastModifiedBy></cp:coreProperties>')
        zf.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:ins w:id="1" w:author="Hacker"><w:r><w:t>Altered Salary</w:t></w:r></w:ins></w:p></w:body></w:document>')
    buf.seek(0)
    docx_bytes = buf.getvalue()

    result = QuickCheckAnalyzer.analyze_file("contract.docx", docx_bytes)
    assert result["file_type"] == "DOCX"
    assert result["verdict"] == "STRONG_EVIDENCE_OF_EDITING"
    assert any("Tracked Changes" in f["title"] for f in result["findings"])

def test_quick_check_api_and_escalate():
    # Log in as screening officer
    login_res = client.post("/api/v1/auth/login", json={"email": "officer@verisight.gov.in", "password": "Officer@12345"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload test image to Quick Check
    img = Image.new('RGB', (100, 100), color=(150, 150, 150))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    buf.seek(0)

    upload_res = client.post(
        "/api/v1/quick-checks",
        files={"file": ("sample_id.jpg", buf.getvalue(), "image/jpeg")},
        headers=headers
    )
    assert upload_res.status_code == 200
    qc_data = upload_res.json()
    assert "check_id" in qc_data
    check_id = qc_data["check_id"]

    # Escalate to full investigation case
    esc_res = client.post(f"/api/v1/quick-checks/{check_id}/escalate", headers=headers)
    assert esc_res.status_code == 200
    esc_data = esc_res.json()
    assert "case_id" in esc_data
    assert "screening_id" in esc_data
