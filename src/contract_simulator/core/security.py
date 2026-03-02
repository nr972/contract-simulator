import os
from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile, status

from contract_simulator.core.config import Settings

# Magic bytes for supported file types
MAGIC_BYTES = {
    ".pdf": b"%PDF",
    ".docx": b"PK\x03\x04",  # ZIP archive (DOCX is a ZIP)
}


async def validate_upload(file: UploadFile, settings: Settings) -> bytes:
    """Validate an uploaded file for security and return its contents.

    Checks: filename presence, extension allowlist, path traversal,
    file size, and magic bytes.

    Raises HTTPException on any validation failure.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    # Sanitize and validate filename — reject path separators
    filename = file.filename
    if any(sep in filename for sep in ("/", "\\", "\x00")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    # Ensure no path traversal via the filename
    safe_name = PurePosixPath(filename).name
    if safe_name != filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    # Check extension
    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    # Read file content (with size limit)
    content = await file.read()

    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty.",
        )

    # Validate magic bytes
    expected_magic = MAGIC_BYTES.get(ext)
    if expected_magic and not content.startswith(expected_magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match its extension.",
        )

    return content
