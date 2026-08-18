from fastapi import APIRouter, Depends
from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.schemas import UsageOut

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get("", response_model=UsageOut)
async def get_usage(user=Depends(get_current_user)):
    db = get_db()
    total = await db.analyses.count_documents({"user_id": user["_id"]})
    return UsageOut(
        free_analyses_remaining=user.get("free_analyses_remaining", 0),
        paid_credits=user.get("paid_credits", 0),
        total_analyses=total,
    )


@router.get("/dashboard")
async def get_dashboard(user=Depends(get_current_user)):
    db = get_db()
    analyses = await db.analyses.find({"user_id": user["_id"]}).sort("created_at", -1).to_list(100)

    total = len(analyses)
    avg_score = round(sum(a["overall_score"] for a in analyses) / total, 1) if total else 0
    best = max(analyses, key=lambda a: a["overall_score"]) if analyses else None
    all_gap_names = {g["skill"] for a in analyses for g in a.get("skill_gaps", [])}

    return {
        "name": user["name"],
        "free_analyses_remaining": user.get("free_analyses_remaining", 0),
        "paid_credits": user.get("paid_credits", 0),
        "total_analyses": total,
        "average_readiness": avg_score,
        "best_matched_role": best.get("target_role") if best else None,
        "skill_gaps_identified": len(all_gap_names),
        "recent_analyses": [
            {
                "id": str(a["_id"]),
                "target_role": a.get("target_role"),
                "overall_score": a["overall_score"],
                "classification": a["classification"],
                "created_at": a["created_at"],
            }
            for a in analyses[:5]
        ],
    }


@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    db = get_db()

    resumes = await db.resumes.find({"user_id": user["_id"]}).sort("created_at", -1).to_list(20)
    job_descriptions = await db.job_descriptions.find({"user_id": user["_id"]}).sort("created_at", -1).to_list(20)
    analyses = await db.analyses.find({"user_id": user["_id"]}).sort("created_at", -1).to_list(20)

    free_remaining = user.get("free_analyses_remaining", 0)
    paid_credits = user.get("paid_credits", 0)
    plan = "Free" if free_remaining > 0 or (free_remaining == 0 and paid_credits == 0) else "Paid"

    return {
        "name": user["name"],
        "email": user["email"],
        "plan": plan,
        "plan_label": "Free trial" if plan == "Free" else "Paid plan",
        "free_analyses_remaining": free_remaining,
        "paid_credits": paid_credits,
        "total_analyses": len(analyses),
        "saved_resumes": [
            {
                "id": str(r["_id"]),
                "filename": r.get("filename", "Resume"),
                "uploaded_at": r.get("created_at"),
                "skills_count": len(r.get("parsed", {}).get("skills", [])),
                "name": r.get("parsed", {}).get("name") or "Unknown",
            }
            for r in resumes
        ],
        "saved_job_descriptions": [
            {
                "id": str(j["_id"]),
                "role": j.get("parsed", {}).get("role") or "Untitled role",
                "company": j.get("parsed", {}).get("company") or "Unknown company",
                "uploaded_at": j.get("created_at"),
                "required_skills_count": len(j.get("parsed", {}).get("required_skills", [])),
            }
            for j in job_descriptions
        ],
        "recent_analyses": [
            {
                "id": str(a["_id"]),
                "target_role": a.get("target_role") or "Untitled role",
                "overall_score": a["overall_score"],
                "classification": a["classification"],
                "created_at": a["created_at"],
            }
            for a in analyses[:5]
        ],
    }
