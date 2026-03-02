import pytest
from fastapi import HTTPException

from contract_simulator.services.parser import (
    extract_text,
    extract_text_from_docx,
    extract_text_from_pdf,
)


def test_extract_text_from_docx(sample_docx_bytes):
    text = extract_text_from_docx(sample_docx_bytes)
    assert "MASTER SERVICES AGREEMENT" in text
    assert "confidentiality" in text.lower()


def test_extract_text_from_pdf(sample_pdf_bytes):
    text = extract_text_from_pdf(sample_pdf_bytes)
    # Minimal PDF may or may not extract cleanly, but shouldn't crash
    assert isinstance(text, str)


def test_extract_text_dispatches_docx(sample_docx_bytes):
    text = extract_text(sample_docx_bytes, "contract.docx")
    assert "MASTER SERVICES AGREEMENT" in text


def test_extract_text_dispatches_pdf(sample_pdf_bytes):
    text = extract_text(sample_pdf_bytes, "contract.pdf")
    assert isinstance(text, str)


def test_extract_text_unsupported_extension():
    with pytest.raises(HTTPException) as exc_info:
        extract_text(b"not a real file", "contract.txt")
    assert exc_info.value.status_code == 400


def test_extract_text_empty_content(sample_docx_bytes):
    """DOCX with no text paragraphs should raise."""
    import io
    import docx

    doc = docx.Document()
    # Add only whitespace paragraphs
    doc.add_paragraph("   ")
    buffer = io.BytesIO()
    doc.save(buffer)
    empty_bytes = buffer.getvalue()

    with pytest.raises(HTTPException) as exc_info:
        extract_text(empty_bytes, "empty.docx")
    assert exc_info.value.status_code == 422
