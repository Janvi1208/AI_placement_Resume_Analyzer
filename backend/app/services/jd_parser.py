import re
from app.models.schemas import JobDescriptionParsed
from app.services.ai_provider import get_ai_provider, wrap_untrusted
from app.services.resume_parser import COMMON_SKILLS

REQUIRED_MARKERS = ["required", "must have", "requirements"]
PREFERRED_MARKERS = ["preferred", "nice to have", "good to have", "bonus"]


async def parse_job_description(raw_text: str, role_hint: str | None = None,
                                  company_hint: str | None = None) -> JobDescriptionParsed:
    lower = raw_text.lower()

    required, preferred = [], []
    for skill in COMMON_SKILLS:
        if skill in lower:
            idx = lower.find(skill)
            window = lower[max(0, idx - 120):idx]
            if any(m in window for m in PREFERRED_MARKERS):
                preferred.append(skill)
            else:
                required.append(skill)  # default bucket = required

    exp_match = re.search(r"(\d+\+?\s*-?\s*\d*\s*years?)", lower)

    parsed = JobDescriptionParsed(
        role=role_hint,
        company=company_hint,
        required_skills=sorted(set(required)),
        preferred_skills=sorted(set(preferred) - set(required)),
        responsibilities=[],
        experience_required=exp_match.group(0) if exp_match else None,
        education_required=[],
        tools=[],
        technologies=sorted(set(required + preferred)),
    )

    provider = get_ai_provider()
    try:
        ai_result = await provider.complete_json(
            prompt=wrap_untrusted("job_description", raw_text),
            schema_hint=(
                "Extract JD fields as JSON matching: role, company, "
                "required_skills[], preferred_skills[], responsibilities[], "
                "experience_required, education_required[], tools[], "
                "technologies[]. Separate required vs preferred skills "
                "clearly."
            ),
        )
        if not ai_result.get("_mock"):
            for field in ("role", "company", "required_skills", "preferred_skills",
                          "responsibilities", "experience_required",
                          "education_required", "tools", "technologies"):
                if ai_result.get(field):
                    setattr(parsed, field, ai_result[field])
    except Exception:
        pass

    return parsed
