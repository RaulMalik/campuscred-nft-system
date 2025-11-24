import io
from datetime import datetime

from PyPDF2 import PdfWriter, PdfReader

from app.services.pdf_signer import PDFSignerService


def _make_dummy_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def test_sign_pdf_adds_metadata_and_returns_bytes(monkeypatch, tmp_path):
    # direct keys into a temp directory to avoid writing into repo
    key_path = tmp_path / "signing_key.pem"
    cert_path = tmp_path / "signing_cert.pem"
    monkeypatch.setenv("PDF_SIGNING_KEY_PATH", str(key_path))
    monkeypatch.setenv("PDF_SIGNING_CERT_PATH", str(cert_path))

    svc = PDFSignerService()
    original = _make_dummy_pdf()

    metadata = {
        "title": "My Title",
        "subject": "My Subject",
    }
    signed = svc.sign_pdf(original, metadata=metadata)

    assert isinstance(signed, bytes)
    assert signed != original  # at least length should differ

    reader = PdfReader(io.BytesIO(signed))
    doc_info = reader.metadata
    # PDF metadata keys are prefixed with '/'
    assert doc_info.get("/Title") == "My Title"
    assert doc_info.get("/Subject") == "My Subject"
    assert "CampusCred" in doc_info.get("/Author", "")


def test_get_certificate_info_has_expected_fields(monkeypatch, tmp_path):
    key_path = tmp_path / "signing_key.pem"
    cert_path = tmp_path / "signing_cert.pem"
    monkeypatch.setenv("PDF_SIGNING_KEY_PATH", str(key_path))
    monkeypatch.setenv("PDF_SIGNING_CERT_PATH", str(cert_path))

    svc = PDFSignerService()
    info = svc.get_certificate_info()
    assert info is not None
    assert "subject" in info
    assert "issuer" in info
    assert "serial_number" in info
    assert "not_before" in info
    assert "not_after" in info