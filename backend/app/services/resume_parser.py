"""
Resume text extraction (PDF/DOCX) + structured parsing.

Parsing uses a hybrid approach: cheap deterministic regex/heuristics for
fields that don't need an LLM (email, phone) plus the AI provider for
free-text sections (skills, experience, projects). When AI_PROVIDER=mock,
we fall back to lightweight heuristics so the app is still usable without
API keys. NEVER invent values that aren't found — missing fields stay
null/empty, per spec section 9.
"""
import re
import io
from pypdf import PdfReader
from docx import Document as DocxDocument

from app.models.schemas import ResumeParsed
from app.services.ai_provider import get_ai_provider, wrap_untrusted

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")

COMMON_SKILLS = [
    "python", "javascript", "typescript", "java", "c++", "sql", "react",
    "next.js", "node.js", "fastapi", "django", "flask", "mongodb",
    "postgresql", "aws", "gcp", "azure", "docker", "kubernetes",
    "machine learning", "deep learning", "nlp", "langchain", "openai",
    "gemini", "mistral", "pandas", "numpy", "pytorch", "tensorflow",
    "git", "rest api", "graphql", "microservices", "ci/cd", "redis",
]

SECTION_HEADERS = {
    "education": ["education", "academic background"],
    "experience": ["experience", "work experience", "employment history"],
    "projects": ["projects", "personal projects"],
    "certifications": ["certifications", "certificates"],
    "achievements": ["achievements", "awards", "accomplishments"],
    "skills": ["skills", "technical skills"],
}


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = DocxDocument(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in doc.paragraphs)


def _split_sections(text: str) -> dict[str, str]:
    lines = text.splitlines()
    sections: dict[str, list[str]] = {k: [] for k in SECTION_HEADERS}
    current = None
    for line in lines:
        low = line.strip().lower()
        matched = None
        for key, headers in SECTION_HEADERS.items():
            if any(low == h or low.startswith(h) for h in headers):
                matched = key
                break
        if matched:
            current = matched
            continue
        if current:
            sections[current].append(line.strip())
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def _extract_bullet_list(section_text: str) -> list[str]:
    if not section_text:
        return []
    items = [ln.strip("-•* \t") for ln in section_text.splitlines() if ln.strip()]
    return [i for i in items if i]


async def parse_resume(raw_text: str) -> ResumeParsed:
    """Deterministic heuristic parse. Swap for `get_ai_provider()` structured
    extraction once a real AI_PROVIDER key is configured — the wrapping
    below already isolates untrusted resume content for that path."""
    email_match = EMAIL_RE.search(raw_text)
    phone_match = PHONE_RE.search(raw_text)

    found_skills = sorted({
        s for s in COMMON_SKILLS if s.lower() in raw_text.lower()
    })

    sections = _split_sections(raw_text)

    # Best-effort name guess: first non-empty line if it doesn't look like
    # contact info. Left null rather than guessed wrong.
    name = None
    for line in raw_text.splitlines()[:5]:
        line = line.strip()
        if line and "@" not in line and not PHONE_RE.search(line) and len(line.split()) <= 5:
            name = line
            break

    parsed = ResumeParsed(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0) if phone_match else None,
        education=_extract_bullet_list(sections.get("education", "")),
        skills=found_skills,
        experience=_extract_bullet_list(sections.get("experience", "")),
        projects=_extract_bullet_list(sections.get("projects", "")),
        certifications=_extract_bullet_list(sections.get("certifications", "")),
        achievements=_extract_bullet_list(sections.get("achievements", "")),
    )

    # Optional AI enrichment hook (no-op under MockProvider):
    provider = get_ai_provider()
    try:
        ai_result = await provider.complete_json(
            prompt=wrap_untrusted("resume", raw_text),
            schema_hint=(
                "Extract resume fields as JSON matching: name, email, phone, "
                "education[], skills[], experience[], projects[], "
                "certifications[], achievements[]. Use null/[] for anything "
                "not explicitly present. Do not invent information."
            ),
        )
        if not ai_result.get("_mock"):
            for field in ("education", "skills", "experience", "projects",
                          "certifications", "achievements"):
                if ai_result.get(field):
                    setattr(parsed, field, ai_result[field])
            if ai_result.get("name"):
                parsed.name = ai_result["name"]
    except Exception:
        pass  # AI enrichment is best-effort; heuristic parse already returned

    return parsed
