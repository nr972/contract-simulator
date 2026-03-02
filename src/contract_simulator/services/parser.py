import io
import os

from fastapi import HTTPException, status


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using pdfplumber."""
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n\n".join(text_parts)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file using python-docx."""
    import docx

    doc = docx.Document(io.BytesIO(file_bytes))
    return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from a file, dispatching based on extension."""
    ext = os.path.splitext(filename)[1].lower()

    extractors = {
        ".pdf": extract_text_from_pdf,
        ".docx": extract_text_from_docx,
    }

    extractor = extractors.get(ext)
    if not extractor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {ext}",
        )

    text = extractor(file_bytes)
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract any text from the uploaded file.",
        )

    return text
