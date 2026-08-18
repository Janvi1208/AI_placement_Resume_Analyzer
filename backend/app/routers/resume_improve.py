from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from pydantic import BaseModel

from app.database import get_db
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/resume", tags=["resume"])


class ResumeImproveRequest(BaseModel):
    resume_id: str
    job_description_id: str | None = None


class ImprovementItem(BaseModel):
    issue_type: str
    detail: str
    suggestion: str


@router.post("/improve", response_model=list[ImprovementItem])
async def improve_resume(payload: ResumeImproveRequest, user=Depends(get_current_user)):
    """Rule-based improvement suggestions. Never invents experience,
    metrics, or technologies not already present (spec section 20) —
    every suggestion here either points at something missing structurally,
    or asks the user to add a REAL metric, never fabricates one."""
    db = get_db()
    resume_doc = await db.resumes.find_one({"_id": ObjectId(payload.resume_id), "user_id": user["_id"]})
    if not resume_doc:
        raise HTTPException(404, "Resume not found.")

    parsed = resume_doc["parsed"]
    issues: list[ImprovementItem] = []

    for bullet in parsed.get("experience", [])[:10]:
        if not any(ch.isdigit() for ch in bullet):
            issues.append(ImprovementItem(
                issue_type="missing_measurable_impact",
                detail=f"Bullet point lacks a metric: \"{bullet[:80]}\"",
                suggestion="If you have a real number (%, time saved, scale, users), add it. Do not invent one.",
            ))

    for project in parsed.get("projects", [])[:10]:
        if len(project.split()) < 8:
            issues.append(ImprovementItem(
                issue_type="poor_project_description",
                detail=f"Project description is too brief: \"{project[:80]}\"",
                suggestion="Expand with what you built, the stack used, and the outcome.",
            ))

    if not parsed.get("email") or not parsed.get("phone"):
        issues.append(ImprovementItem(
            issue_type="ats_issue",
            detail="Missing clear contact information.",
            suggestion="Ensure email and phone are present in plain text (not inside images) for ATS parsing.",
        ))

    if not parsed.get("skills"):
        issues.append(ImprovementItem(
            issue_type="missing_relevant_keywords",
            detail="No clearly-parsed skills section found.",
            suggestion="Add an explicit 'Skills' section listing technologies you've actually used.",
        ))

    if not issues:
        issues.append(ImprovementItem(
            issue_type="none",
            detail="No major structural issues found.",
            suggestion="Resume structure looks solid — focus on tailoring keywords per job description.",
        ))

    return issues
