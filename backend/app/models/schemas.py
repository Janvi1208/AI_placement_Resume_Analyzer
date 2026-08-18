"""
Pydantic request/response schemas. Kept in one module for a project this size;
split into per-domain files as it grows (see README 'What remains').
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime


# ---------- Auth ----------

class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: EmailStr
    free_analyses_remaining: int
    paid_credits: int
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Resume ----------

class ResumeParsed(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    education: list[str] = []
    skills: list[str] = []
    experience: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []
    achievements: list[str] = []


class ResumeUploadOut(BaseModel):
    id: str
    filename: str
    size_bytes: int
    parsed: ResumeParsed


# ---------- Job Description ----------

class JobDescriptionIn(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    raw_text: Optional[str] = None
    url: Optional[str] = None


class JobDescriptionParsed(BaseModel):
    role: Optional[str] = None
    company: Optional[str] = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    responsibilities: list[str] = []
    experience_required: Optional[str] = None
    education_required: list[str] = []
    tools: list[str] = []
    technologies: list[str] = []


class JobDescriptionOut(BaseModel):
    id: str
    parsed: JobDescriptionParsed


# ---------- Analysis ----------

class AnalyzeRequest(BaseModel):
    resume_id: str
    job_description_id: str
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    preparation_deadline_days: Optional[int] = None


class SkillMatch(BaseModel):
    skill: str
    match_type: Literal["exact", "related", "partial", "missing"]
    confidence: float
    evidence: Optional[str] = None


class SkillGap(BaseModel):
    skill: str
    priority: Literal["critical", "high", "medium", "low"]
    reason: str


class ScoreBreakdown(BaseModel):
    technical_skills: float
    ai_ml_skills: float
    jd_alignment: float
    experience: float
    projects: float
    resume_quality: float


class AnalysisOut(BaseModel):
    id: str
    overall_score: float
    classification: str
    breakdown: ScoreBreakdown
    matching_skills: list[SkillMatch]
    skill_gaps: list[SkillGap]
    recommendations: list[str]
    created_at: datetime


# ---------- Interview ----------

class InterviewQuestion(BaseModel):
    id: str
    category: Literal[
        "hr", "resume", "technical", "ai_ml",
        "system_design", "project_based", "missing_skill"
    ]
    question: str
    why_selected: str


class InterviewStartRequest(BaseModel):
    analysis_id: str


class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str


class InterviewFeedback(BaseModel):
    technical_accuracy: float
    communication: float
    depth: float
    relevance: float
    overall: float
    feedback_text: str
    next_question: Optional[InterviewQuestion] = None


# ---------- Roadmap ----------

class RoadmapRequest(BaseModel):
    analysis_id: str
    duration_days: Literal[3, 7, 14, 30]


class RoadmapDay(BaseModel):
    day: int
    topics: list[str]
    maps_to_gap: list[str]


class RoadmapOut(BaseModel):
    id: str
    duration_days: int
    days: list[RoadmapDay]


# ---------- Payments ----------

class CreateOrderRequest(BaseModel):
    pass  # price comes from server config, never trust client input


class CreateOrderOut(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class UsageOut(BaseModel):
    free_analyses_remaining: int
    paid_credits: int
    total_analyses: int
