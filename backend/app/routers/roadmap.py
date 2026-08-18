from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.schemas import RoadmapRequest, RoadmapOut, SkillGap
from app.services.insights import build_roadmap

router = APIRouter(prefix="/api/v1/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=RoadmapOut)
async def generate_roadmap(payload: RoadmapRequest, user=Depends(get_current_user)):
    db = get_db()
    analysis = await db.analyses.find_one({"_id": ObjectId(payload.analysis_id), "user_id": user["_id"]})
    if not analysis:
        raise HTTPException(404, "Analysis not found.")

    gaps = [SkillGap(**g) for g in analysis["skill_gaps"]]
    days = build_roadmap(gaps, payload.duration_days)

    doc = {
        "user_id": user["_id"],
        "analysis_id": analysis["_id"],
        "duration_days": payload.duration_days,
        "days": [d.model_dump() for d in days],
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.roadmaps.insert_one(doc)

    return RoadmapOut(id=str(result.inserted_id), duration_days=payload.duration_days, days=days)
