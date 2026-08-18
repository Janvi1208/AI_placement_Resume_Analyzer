from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
import traceback

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.services.usage import consume_entitlement, refund_entitlement
from app.services.matching import match_skills
from app.services.scoring import compute_score
from app.services.insights import build_skill_gaps, build_recommendations
from app.models.schemas import (
    AnalyzeRequest,
    AnalysisOut,
    ResumeParsed,
    JobDescriptionParsed,
)

router = APIRouter(
    prefix="/api/v1/analyze",
    tags=["analyze"],
)


def _require_object_id(value: str, field_name: str) -> ObjectId:
    """
    Convert a string into a MongoDB ObjectId.
    """
    try:
        return ObjectId(value)
    except (InvalidId, TypeError, ValueError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {field_name} id.",
        )


def _convert_items_to_strings(items):
    """
    Convert structured dictionaries/lists into strings.

    ResumeParsed currently expects fields such as:
        education: list[str]
        projects: list[str]
        certifications: list[str]

    But MongoDB may contain dictionaries for these fields.
    This function converts them safely into readable strings.
    """

    if not items:
        return []

    result = []

    for item in items:
        if isinstance(item, dict):
            parts = []

            for key, value in item.items():
                if value is None:
                    continue

                # Convert nested dictionaries/lists to strings safely
                if isinstance(value, (dict, list)):
                    value = str(value)

                parts.append(
                    f"{key.replace('_', ' ').title()}: {value}"
                )

            result.append(", ".join(parts))

        elif isinstance(item, list):
            result.append(", ".join(str(x) for x in item))

        else:
            result.append(str(item))

    return result


@router.post(
    "/readiness",
    response_model=AnalysisOut,
)
async def analyze_readiness(
    payload: AnalyzeRequest,
    user=Depends(get_current_user),
):
    db = get_db()

    # =========================================================
    # 1. Validate Resume ID
    # =========================================================

    resume_id = _require_object_id(
        payload.resume_id,
        "resume",
    )

    # =========================================================
    # 2. Validate Job Description ID
    # =========================================================

    job_description_id = _require_object_id(
        payload.job_description_id,
        "job description",
    )

    # =========================================================
    # 3. Find Resume
    # =========================================================

    resume_doc = await db.resumes.find_one(
        {
            "_id": resume_id,
            "user_id": user["_id"],
        }
    )

    if not resume_doc:
        raise HTTPException(
            status_code=404,
            detail="Resume not found.",
        )

    # =========================================================
    # 4. Find Job Description
    # =========================================================

    jd_doc = await db.job_descriptions.find_one(
        {
            "_id": job_description_id,
            "user_id": user["_id"],
        }
    )

    if not jd_doc:
        raise HTTPException(
            status_code=404,
            detail="Job description not found.",
        )

    # =========================================================
    # 5. Consume User Entitlement
    # =========================================================

    entitlement_kind = await consume_entitlement(
        user["_id"]
    )

    try:

        # =====================================================
        # 6. Validate Resume Parsed Data
        # =====================================================

        if "parsed" not in resume_doc:
            raise ValueError(
                "Resume document does not contain 'parsed' data."
            )

        resume_data = resume_doc["parsed"].copy()

        # =====================================================
        # 7. Convert Structured Resume Data
        # =====================================================
        #
        # MongoDB may contain:
        #
        # education: [
        #     {
        #         "institution": "...",
        #         "degree": "...",
        #         "score": "..."
        #     }
        # ]
        #
        # But ResumeParsed expects list[str].
        #
        # Therefore we convert dictionaries into strings.
        # =====================================================

        resume_data["education"] = _convert_items_to_strings(
            resume_data.get("education", [])
        )

        resume_data["projects"] = _convert_items_to_strings(
            resume_data.get("projects", [])
        )

        resume_data["certifications"] = _convert_items_to_strings(
            resume_data.get("certifications", [])
        )

        # =====================================================
        # 8. Create ResumeParsed Object
        # =====================================================

        resume = ResumeParsed(
            **resume_data
        )

        # =====================================================
        # 9. Validate Job Description Parsed Data
        # =====================================================

        if "parsed" not in jd_doc:
            raise ValueError(
                "Job description document does not contain "
                "'parsed' data."
            )

        jd_data = jd_doc["parsed"].copy()

        # =====================================================
        # 10. Create JobDescriptionParsed Object
        # =====================================================

        jd = JobDescriptionParsed(
            **jd_data
        )

        # =====================================================
        # 11. Match Resume Skills With Job Skills
        # =====================================================

        matches = match_skills(
            resume.skills,
            jd.required_skills,
            jd.preferred_skills,
        )

        # =====================================================
        # 12. Calculate Readiness Score
        # =====================================================

        (
            overall_score,
            classification,
            breakdown,
        ) = compute_score(
            resume,
            jd,
            matches,
            raw_text_len=len(
                resume_doc.get(
                    "raw_text",
                    "",
                )
            ),
        )

        # =====================================================
        # 13. Calculate Skill Gaps
        # =====================================================

        gaps = build_skill_gaps(
            matches,
            jd,
        )

        # =====================================================
        # 14. Generate Recommendations
        # =====================================================

        recommendations = build_recommendations(
            gaps,
            resume,
        )

        # =====================================================
        # 15. Create Analysis Document
        # =====================================================

        analysis_doc = {
            "user_id": user["_id"],

            "resume_id": resume_doc["_id"],

            "job_description_id": jd_doc["_id"],

            "target_role": (
                payload.target_role
                if payload.target_role
                else jd.role
            ),

            "experience_level": (
                payload.experience_level
            ),

            "overall_score": overall_score,

            "classification": classification,

            "breakdown": breakdown.model_dump(),

            "matching_skills": [
                match.model_dump()
                for match in matches
            ],

            "skill_gaps": [
                gap.model_dump()
                for gap in gaps
            ],

            "recommendations": recommendations,

            "entitlement_used": entitlement_kind,

            "created_at": datetime.now(
                timezone.utc
            ),
        }

        # =====================================================
        # 16. Save Analysis To MongoDB
        # =====================================================

        result = await db.analyses.insert_one(
            analysis_doc
        )

        # =====================================================
        # 17. Save Usage Information
        # =====================================================

        await db.usage.insert_one(
            {
                "user_id": user["_id"],

                "analysis_id": result.inserted_id,

                "type": entitlement_kind,

                "created_at": datetime.now(
                    timezone.utc
                ),
            }
        )

        # =====================================================
        # 18. Return Analysis Result
        # =====================================================

        return AnalysisOut(
            id=str(
                result.inserted_id
            ),

            overall_score=overall_score,

            classification=classification,

            breakdown=breakdown,

            matching_skills=matches,

            skill_gaps=gaps,

            recommendations=recommendations,

            created_at=analysis_doc[
                "created_at"
            ],
        )

    # =========================================================
    # Handle Expected HTTP Errors
    # =========================================================

    except HTTPException:

        try:
            await refund_entitlement(
                user["_id"],
                entitlement_kind,
            )
        except Exception as refund_error:
            print(
                "Refund error:",
                str(refund_error),
            )

        raise

    # =========================================================
    # Handle Unexpected Errors
    # =========================================================

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("ANALYSIS PIPELINE ERROR")
        print("=" * 70)

        print(
            "Error Type:",
            type(error).__name__,
        )

        print(
            "Error Message:",
            str(error),
        )

        print("-" * 70)

        traceback.print_exc()

        print("=" * 70)
        print("\n")

        # =====================================================
        # Refund User Credit
        # =====================================================

        try:

            await refund_entitlement(
                user["_id"],
                entitlement_kind,
            )

        except Exception as refund_error:

            print(
                "REFUND ERROR:",
                str(refund_error),
            )

            traceback.print_exc()

        # =====================================================
        # Return Error To Frontend
        # =====================================================

        raise HTTPException(
            status_code=500,
            detail=(
                "Analysis failed: "
                + str(error)
            ),
        ) from error


# =============================================================
# GET SINGLE ANALYSIS
# =============================================================

@router.get(
    "/{analysis_id}",
    response_model=AnalysisOut,
)
async def get_analysis(
    analysis_id: str,
    user=Depends(get_current_user),
):
    db = get_db()

    # Validate analysis ID

    analysis_object_id = _require_object_id(
        analysis_id,
        "analysis",
    )

    # Find analysis

    doc = await db.analyses.find_one(
        {
            "_id": analysis_object_id,
            "user_id": user["_id"],
        }
    )

    if not doc:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    # Return analysis

    return AnalysisOut(
        id=str(
            doc["_id"]
        ),

        overall_score=doc[
            "overall_score"
        ],

        classification=doc[
            "classification"
        ],

        breakdown=doc[
            "breakdown"
        ],

        matching_skills=doc[
            "matching_skills"
        ],

        skill_gaps=doc[
            "skill_gaps"
        ],

        recommendations=doc[
            "recommendations"
        ],

        created_at=doc[
            "created_at"
        ],
    )


# =============================================================
# GET ALL ANALYSES
# =============================================================

@router.get(
    "",
    response_model=list[AnalysisOut],
)
async def list_analyses(
    user=Depends(get_current_user),
):
    db = get_db()

    cursor = (
        db.analyses
        .find(
            {
                "user_id": user["_id"],
            }
        )
        .sort(
            "created_at",
            -1,
        )
    )

    docs = await cursor.to_list(
        length=100
    )

    return [
        AnalysisOut(
            id=str(
                doc["_id"]
            ),

            overall_score=doc[
                "overall_score"
            ],

            classification=doc[
                "classification"
            ],

            breakdown=doc[
                "breakdown"
            ],

            matching_skills=doc[
                "matching_skills"
            ],

            skill_gaps=doc[
                "skill_gaps"
            ],

            recommendations=doc[
                "recommendations"
            ],

            created_at=doc[
                "created_at"
            ],
        )

        for doc in docs
    ]