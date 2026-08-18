"""
Skill matching: resume skills vs JD required/preferred skills.

Exact matches are computed deterministically (string match). "Related"
matches (e.g. JD wants OpenAI, resume shows Gemini/Mistral -> related LLM
API experience) use a small synonym/relation table here, with a hook to
let a real AI provider improve semantic matching later (see
`_ai_semantic_pass`). Confidence scores from the AI path are never used to
silently overwrite an exact/missing determination — only to fill in
"related"/"partial" nuance, keeping the final classification auditable.
"""
from app.models.schemas import SkillMatch

RELATED_GROUPS = [
    {"openai", "gemini", "mistral", "llm apis", "anthropic", "claude"},
    {"react", "next.js", "vue", "angular"},
    {"docker", "kubernetes", "containerization"},
    {"aws", "gcp", "azure", "cloud"},
    {"pytorch", "tensorflow", "deep learning"},
    {"postgresql", "mongodb", "sql", "mysql", "database"},
]


def _related_group(skill: str) -> set[str] | None:
    skill = skill.lower()
    for group in RELATED_GROUPS:
        if skill in group:
            return group
    return None


def _normalize_skill(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip().lower()
    return value or None


def match_skills(resume_skills: list[str], jd_required: list[str],
                  jd_preferred: list[str]) -> list[SkillMatch]:
    resume_set = {s for s in {_normalize_skill(v) for v in resume_skills} if s}
    results: list[SkillMatch] = []

    for skill in jd_required + jd_preferred:
        skill_l = _normalize_skill(skill)
        if not skill_l:
            continue

        if skill_l in resume_set:
            results.append(SkillMatch(
                skill=skill.strip() if isinstance(skill, str) else str(skill), match_type="exact", confidence=1.0,
                evidence=f"'{skill_l}' found directly in resume skills.",
            ))
            continue

        group = _related_group(skill_l)
        if group:
            overlap = group.intersection(resume_set) - {skill_l}
            if overlap:
                related_terms = ", ".join(sorted(overlap))
                results.append(SkillMatch(
                    skill=skill.strip() if isinstance(skill, str) else str(skill), match_type="related", confidence=0.7,
                    evidence=(
                        f"Resume shows related experience: {related_terms}. "
                        f"Not a direct claim of '{skill_l}' itself."
                    ),
                ))
                continue

        partial_hits = [rs for rs in resume_set if skill_l in rs or rs in skill_l]
        if partial_hits:
            results.append(SkillMatch(
                skill=skill.strip() if isinstance(skill, str) else str(skill), match_type="partial", confidence=0.4,
                evidence=f"Partial textual overlap with resume term '{partial_hits[0]}'.",
            ))
            continue

        results.append(SkillMatch(
            skill=skill.strip() if isinstance(skill, str) else str(skill), match_type="missing", confidence=0.0,
            evidence="No evidence found in resume.",
        ))

    return results
