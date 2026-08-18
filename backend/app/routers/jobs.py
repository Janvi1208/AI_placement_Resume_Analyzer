from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId
import httpx
import re

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.schemas import JobDescriptionIn, JobDescriptionOut
from app.services.jd_parser import parse_job_description

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])

TAG_RE = re.compile(r"<[^>]+>")


async def _safe_extract_from_url(url: str) -> str:
    """Best-effort, respectful extraction: simple GET with a real user
    agent, strip HTML tags. No bypassing of paywalls/robots, no headless
    browser automation — kept intentionally minimal per 'respecting
    website terms' in the spec."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; PlacementAnalyzer/1.0)"})
            resp.raise_for_status()
            text = TAG_RE.sub(" ", resp.text)
            return re.sub(r"\s+", " ", text).strip()[:20000]
    except Exception:
        raise HTTPException(422, "Could not extract job description from that URL. Please paste the text directly.")


@router.post("", response_model=JobDescriptionOut)
async def create_job_description(payload: JobDescriptionIn, user=Depends(get_current_user)):
    raw_text = payload.raw_text
    if not raw_text and payload.url:
        raw_text = await _safe_extract_from_url(payload.url)

    if not raw_text or not raw_text.strip():
        raise HTTPException(400, "Provide either job description text or a URL.")

    parsed = await parse_job_description(raw_text, role_hint=payload.role, company_hint=payload.company)

    db = get_db()
    doc = {
        "user_id": user["_id"],
        "raw_text": raw_text,
        "source_url": payload.url,
        "parsed": parsed.model_dump(),
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.job_descriptions.insert_one(doc)
    return JobDescriptionOut(id=str(result.inserted_id), parsed=parsed)


@router.get("/{jd_id}", response_model=JobDescriptionOut)
async def get_job_description(jd_id: str, user=Depends(get_current_user)):
    db = get_db()
    doc = await db.job_descriptions.find_one({"_id": ObjectId(jd_id), "user_id": user["_id"]})
    if not doc:
        raise HTTPException(404, "Job description not found.")
    return JobDescriptionOut(id=str(doc["_id"]), parsed=doc["parsed"])
