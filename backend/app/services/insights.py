"""
Downstream insight generation that consumes the deterministic score +
skill matches: gap prioritization, recommendations, interview questions,
and the preparation roadmap. These lean on the AI provider for natural
language, but priority/mapping logic itself stays deterministic so gaps
and roadmap topics are always traceable back to an actual JD requirement
(spec section 19: "Every topic should map to an identified job
requirement or skill gap").
"""
import uuid
from app.models.schemas import (
    SkillMatch, SkillGap, InterviewQuestion, RoadmapDay,
    ResumeParsed, JobDescriptionParsed,
)
from app.services.jd_parser import JobDescriptionParsed as _JD  # noqa: F401


def build_skill_gaps(matches: list[SkillMatch], jd: JobDescriptionParsed) -> list[SkillGap]:
    required_set = {s.lower() for s in jd.required_skills}
    gaps: list[SkillGap] = []

    for m in matches:
        if m.match_type == "missing":
            priority = "critical" if m.skill.lower() in required_set else "high"
            reason = (
                "Required but not demonstrated in resume."
                if priority == "critical"
                else "Preferred and no evidence found."
            )
        elif m.match_type == "partial":
            priority = "high" if m.skill.lower() in required_set else "medium"
            reason = "Some related knowledge exists but limited direct evidence."
        elif m.match_type == "related":
            priority = "medium"
            reason = "Related experience exists; direct hands-on evidence would strengthen this."
        else:
            continue  # exact matches are not gaps

        gaps.append(SkillGap(skill=m.skill, priority=priority, reason=reason))

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda g: order[g.priority])
    return gaps


def build_recommendations(gaps: list[SkillGap], resume: ResumeParsed) -> list[str]:
    recs = []
    for gap in gaps[:6]:
        if gap.priority == "critical":
            recs.append(
                f"Build a small, demonstrable project using {gap.skill} — "
                f"this is a required skill with zero current evidence."
            )
        elif gap.priority == "high":
            recs.append(
                f"Add specific, named experience with {gap.skill} to your "
                f"resume if you have it, or gain hands-on practice."
            )
        else:
            recs.append(
                f"Strengthen your {gap.skill} evidence with a concrete "
                f"example or metric in your resume."
            )
    if not resume.projects:
        recs.append("Add at least 1-2 projects with measurable outcomes — none were found on your resume.")
    if not resume.certifications:
        recs.append("Consider a relevant certification to validate skills that lack project evidence.")
    return recs


QUESTION_TEMPLATES = {
    "hr": "Tell me about a time you worked under a tight deadline. How did you handle it?",
    "resume": "Walk me through the most impactful project on your resume — what was your specific contribution?",
}


def build_interview_questions(resume: ResumeParsed, jd: JobDescriptionParsed,
                                gaps: list[SkillGap]) -> list[InterviewQuestion]:
    questions: list[InterviewQuestion] = []

    questions.append(InterviewQuestion(
        id=str(uuid.uuid4()), category="hr", question=QUESTION_TEMPLATES["hr"],
        why_selected="Standard behavioral question to assess communication and ownership.",
    ))
    questions.append(InterviewQuestion(
        id=str(uuid.uuid4()), category="resume", question=QUESTION_TEMPLATES["resume"],
        why_selected="Based directly on your resume content to verify depth of contribution.",
    ))

    for project in resume.projects[:2]:
        questions.append(InterviewQuestion(
            id=str(uuid.uuid4()), category="project_based",
            question=f"In your project '{project[:60]}', what was the hardest technical decision and why?",
            why_selected=f"Selected from your resume's project section: '{project[:60]}'.",
        ))

    for skill in jd.required_skills[:2]:
        questions.append(InterviewQuestion(
            id=str(uuid.uuid4()), category="technical",
            question=f"How would you use {skill} to solve a real-world problem relevant to this role?",
            why_selected=f"'{skill}' is a required skill in the job description.",
        ))

    for gap in [g for g in gaps if g.priority in ("critical", "high")][:3]:
        questions.append(InterviewQuestion(
            id=str(uuid.uuid4()), category="missing_skill",
            question=f"This role expects {gap.skill}. How would you ramp up on it quickly if hired?",
            why_selected=f"Identified skill gap: {gap.reason}",
        ))

    questions.append(InterviewQuestion(
        id=str(uuid.uuid4()), category="system_design",
        question=f"How would you design a scalable system for a typical {jd.role or 'this'} workload?",
        why_selected="System design question tailored to the target role.",
    ))

    return questions


def build_roadmap(gaps: list[SkillGap], duration_days: int) -> list[RoadmapDay]:
    priority_gaps = [g for g in gaps if g.priority in ("critical", "high", "medium")]
    if not priority_gaps:
        priority_gaps = gaps or [SkillGap(skill="General interview practice", priority="low", reason="No major gaps identified.")]

    # Reserve the final day for review/mock-interview only when there's more
    # than one day, so short (3-day) plans still get real study time.
    study_days = duration_days - 1 if duration_days > 1 else duration_days
    study_days = max(1, study_days)

    # Distribute gaps round-robin across study days so every gap gets
    # covered at least once before any gap repeats (avoids the same topic
    # being assigned to every remaining day once the gap list is shorter
    # than the number of days).
    buckets: list[list[SkillGap]] = [[] for _ in range(study_days)]
    for i, gap in enumerate(priority_gaps):
        buckets[i % study_days].append(gap)

    # If there were fewer gaps than study days, some buckets are empty —
    # backfill those with a light review pass over all gaps instead of
    # leaving a day with nothing to do.
    for b in buckets:
        if not b:
            b.append(priority_gaps[0])

    days: list[RoadmapDay] = []
    for day_num in range(1, study_days + 1):
        day_gaps = buckets[day_num - 1]
        topics = [f"Study & practice: {g.skill}" for g in day_gaps]
        days.append(RoadmapDay(
            day=day_num, topics=topics,
            maps_to_gap=[g.skill for g in day_gaps],
        ))

    if duration_days > 1:
        days.append(RoadmapDay(
            day=duration_days,
            topics=["Full mock interview", "Resume final review", "Revisit weakest topic from earlier days"],
            maps_to_gap=[g.skill for g in priority_gaps],
        ))

    return days
