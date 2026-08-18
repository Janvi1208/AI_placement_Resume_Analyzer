from fastapi import UploadFile, HTTPException
from app.config import get_settings

settings = get_settings()


async def validate_and_read(file: UploadFile) -> bytes:
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed = settings.allowed_resume_extensions.split(",")
    if ext not in allowed:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {allowed}")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(400, f"File too large ({size_mb:.1f}MB). Max {settings.max_upload_size_mb}MB.")

    if len(contents) == 0:
        raise HTTPException(400, "Uploaded file is empty.")

    # Magic-byte sanity check (defense in depth beyond extension trust)
    if ext == ".pdf" and not contents.startswith(b"%PDF"):
        raise HTTPException(400, "File does not appear to be a valid PDF.")
    if ext == ".docx" and not contents[:2] == b"PK":
        raise HTTPException(400, "File does not appear to be a valid DOCX.")

    return contents
