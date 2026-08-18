from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.schemas import (
    InterviewStartRequest, InterviewAnswerRequest, InterviewFeedback,
    ResumeParsed, JobDescriptionParsed, SkillGap,
)
from app.services.insights import build_interview_questions

router = APIRouter(prefix="/api/v1/interview", tags=["interview"])


@router.post("/start")
async def start_interview(payload: InterviewStartRequest, user=Depends(get_current_user)):
    db = get_db()
    analysis = await db.analyses.find_one({"_id": ObjectId(payload.analysis_id), "user_id": user["_id"]})
    if not analysis:
        raise HTTPException(404, "Analysis not found.")

    resume_doc = await db.resumes.find_one({"_id": analysis["resume_id"]})
    jd_doc = await db.job_descriptions.find_one({"_id": analysis["job_description_id"]})

    resume = ResumeParsed(**resume_doc["parsed"])
    jd = JobDescriptionParsed(**jd_doc["parsed"])
    gaps = [SkillGap(**g) for g in analysis["skill_gaps"]]

    questions = build_interview_questions(resume, jd, gaps)

    session_doc = {
        "user_id": user["_id"],
        "analysis_id": analysis["_id"],
        "questions": [q.model_dump() for q in questions],
        "current_index": 0,
        "answers": [],
        "created_at": datetime.now(timezone.utc),
        "completed": False,
    }
    result = await db.interview_sessions.insert_one(session_doc)

    return {
        "session_id": str(result.inserted_id),
        "total_questions": len(questions),
        "question": questions[0],
    }


def _evaluate_answer_deterministic(answer: str) -> dict:
    """Lightweight deterministic scoring stand-in used when AI_PROVIDER=mock.
    Swap for an AI-provider call for real qualitative evaluation — keep the
    same 0-100 scale and field names so the frontend doesn't need to change."""
    length_score = min(100, len(answer.split()) * 4)
    has_example = any(w in answer.lower() for w in ["example", "for instance", "specifically", "project"])
    base = length_score * 0.6 + (20 if has_example else 0)
    base = min(100, max(10, base))
    return {
        "technical_accuracy": round(base * 0.9, 1),
        "communication": round(min(100, base + 10), 1),
        "depth": round(base * 0.85, 1),
        "relevance": round(min(100, base + 5), 1),
        "overall": round(base, 1),
    }


@router.post("/answer", response_model=InterviewFeedback)
async def answer_question(payload: InterviewAnswerRequest, user=Depends(get_current_user)):
    db = get_db()
    session = await db.interview_sessions.find_one({"_id": ObjectId(payload.session_id), "user_id": user["_id"]})
    if not session:
        raise HTTPException(404, "Interview session not found.")
    if session["completed"]:
        raise HTTPException(400, "This interview session is already complete.")

    scores = _evaluate_answer_deterministic(payload.answer)

    await db.interview_answers.insert_one({
        "session_id": session["_id"],
        "question_id": payload.question_id,
        "answer": payload.answer,
        "scores": scores,
        "created_at": datetime.now(timezone.utc),
    })

    questions = session["questions"]
    next_index = session["current_index"] + 1
    next_question = None
    completed = next_index >= len(questions)

    await db.interview_sessions.update_one(
        {"_id": session["_id"]},
        {"$set": {"current_index": next_index, "completed": completed}},
    )

    if not completed:
        next_question = questions[next_index]

    feedback_text = (
        "Solid, specific answer with concrete detail." if scores["overall"] >= 70
        else "Reasonable answer — try adding a specific example or metric to strengthen it."
    )

    return InterviewFeedback(
        **scores, feedback_text=feedback_text,
        next_question=next_question,
    )


@router.get("/{session_id}")
async def get_session(session_id: str, user=Depends(get_current_user)):
    db = get_db()
    session = await db.interview_sessions.find_one({"_id": ObjectId(session_id), "user_id": user["_id"]})
    if not session:
        raise HTTPException(404, "Interview session not found.")

    answers = await db.interview_answers.find({"session_id": session["_id"]}).to_list(100)

    if answers:
        avg = lambda k: round(sum(a["scores"][k] for a in answers) / len(answers), 1)
        summary = {
            "technical_accuracy": avg("technical_accuracy"),
            "communication": avg("communication"),
            "depth": avg("depth"),
            "relevance": avg("relevance"),
            "overall": avg("overall"),
        }
    else:
        summary = None

    return {
        "session_id": str(session["_id"]),
        "completed": session["completed"],
        "total_questions": len(session["questions"]),
        "answered": len(answers),
        "summary": summary,
    }
