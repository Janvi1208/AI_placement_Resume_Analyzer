from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.utils.file_validation import validate_and_read
from app.services.resume_parser import extract_text_from_pdf, extract_text_from_docx, parse_resume
from app.models.schemas import ResumeUploadOut

router = APIRouter(prefix="/api/v1/resume", tags=["resume"])


@router.post("/upload", response_model=ResumeUploadOut)
async def upload_resume(file: UploadFile = File(...), user=Depends(get_current_user)):
    contents = await validate_and_read(file)
    ext = file.filename.rsplit(".", 1)[-1].lower()

    try:
        if ext == "pdf":
            raw_text = extract_text_from_pdf(contents)
        elif ext == "docx":
            raw_text = extract_text_from_docx(contents)
        else:
            raise HTTPException(400, "Unsupported file type.")
    except Exception:
        raise HTTPException(422, "Could not read this file — it may be corrupted or scanned/image-only.")

    if not raw_text.strip():
        raise HTTPException(422, "No extractable text found in this document.")

    parsed = await parse_resume(raw_text)

    db = get_db()
    doc = {
        "user_id": user["_id"],
        "filename": file.filename,
        "size_bytes": len(contents),
        "raw_text": raw_text,
        "parsed": parsed.model_dump(),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.resumes.insert_one(doc)

    return ResumeUploadOut(
        id=str(result.inserted_id),
        filename=file.filename,
        size_bytes=len(contents),
        parsed=parsed,
    )


@router.get("/{resume_id}", response_model=ResumeUploadOut)
async def get_resume(resume_id: str, user=Depends(get_current_user)):
    db = get_db()
    doc = await db.resumes.find_one({"_id": ObjectId(resume_id), "user_id": user["_id"]})
    if not doc:
        raise HTTPException(404, "Resume not found.")
    return ResumeUploadOut(
        id=str(doc["_id"]), filename=doc["filename"],
        size_bytes=doc["size_bytes"], parsed=doc["parsed"],
    )
