"""
Deterministic readiness scoring.

Per spec section 12 / product rule #4: the LLM never chooses the final
numeric score. This module computes it from structured inputs only, using
weights pulled from Settings (configurable, not hard-coded — rule #11).
"""
from app.config import get_settings
from app.models.schemas import SkillMatch, ScoreBreakdown, ResumeParsed, JobDescriptionParsed

settings = get_settings()

AI_ML_TERMS = {
    "machine learning", "deep learning", "nlp", "langchain", "openai",
    "gemini", "mistral", "pytorch", "tensorflow", "llm apis",
}

MATCH_WEIGHT = {"exact": 1.0, "related": 0.7, "partial": 0.4, "missing": 0.0}


def _skills_score(matches: list[SkillMatch], only: set[str] | None = None) -> float:
    relevant = matches
    if only is not None:
        relevant = [m for m in matches if m.skill.lower() in only]
    if not relevant:
        return 100.0 if only else 0.0
    total = sum(MATCH_WEIGHT[m.match_type] for m in relevant)
    return round((total / len(relevant)) * 100, 1)


def _jd_alignment_score(matches: list[SkillMatch]) -> float:
    if not matches:
        return 0.0
    total = sum(MATCH_WEIGHT[m.match_type] for m in matches)
    return round((total / len(matches)) * 100, 1)


def _experience_score(resume: ResumeParsed, jd: JobDescriptionParsed) -> float:
    # Deterministic heuristic: presence + volume of experience entries.
    n = len(resume.experience)
    if n == 0:
        return 20.0
    return round(min(100.0, 40 + n * 15), 1)


def _projects_score(resume: ResumeParsed) -> float:
    n = len(resume.projects)
    if n == 0:
        return 15.0
    return round(min(100.0, 30 + n * 20), 1)


def _resume_quality_score(resume: ResumeParsed, raw_text_len: int) -> float:
    score = 50.0
    if resume.email:
        score += 10
    if resume.phone:
        score += 5
    if resume.skills:
        score += 10
    if resume.experience:
        score += 10
    if resume.projects:
        score += 10
    if raw_text_len > 1500:
        score += 5
    return round(min(100.0, score), 1)


def compute_score(resume: ResumeParsed, jd: JobDescriptionParsed,
                   matches: list[SkillMatch], raw_text_len: int
                   ) -> tuple[float, str, ScoreBreakdown]:
    technical = _skills_score(matches)
    ai_ml = _skills_score(matches, only=AI_ML_TERMS)
    jd_alignment = _jd_alignment_score(matches)
    experience = _experience_score(resume, jd)
    projects = _projects_score(resume)
    resume_quality = _resume_quality_score(resume, raw_text_len)

    weighted = (
        technical * settings.weight_technical_skills
        + ai_ml * settings.weight_ai_ml_skills
        + jd_alignment * settings.weight_jd_alignment
        + experience * settings.weight_experience
        + projects * settings.weight_projects
        + resume_quality * settings.weight_resume_quality
    )
    overall = round(weighted, 1)

    if overall < 40:
        classification = "Needs Significant Preparation"
    elif overall < 60:
        classification = "Needs Preparation"
    elif overall < 75:
        classification = "Moderate Readiness"
    elif overall < 90:
        classification = "Strong Candidate"
    else:
        classification = "Excellent Match"

    breakdown = ScoreBreakdown(
        technical_skills=technical,
        ai_ml_skills=ai_ml,
        jd_alignment=jd_alignment,
        experience=experience,
        projects=projects,
        resume_quality=resume_quality,
    )
    return overall, classification, breakdown
