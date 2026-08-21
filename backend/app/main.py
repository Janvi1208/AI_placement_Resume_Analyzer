
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
except Exception:
    # Fallback if slowapi is not installed
    class RateLimitExceeded(Exception):
        pass

    def get_remote_address(request=None):
        return "local"

    class Limiter:
        def __init__(self, *args, **kwargs):
            pass

    def _rate_limit_exceeded_handler(request, exc):
        return JSONResponse(
            status_code=429,
            content={"detail": "rate limit exceeded"},
        )


from app.config import get_settings
from app.database import init_indexes

from app.routers import (
    auth,
    resume,
    jobs,
    analyze,
    interview,
    roadmap,
    resume_improve,
    payments,
    usage,
)


# --------------------------------------------------
# Settings
# --------------------------------------------------

settings = get_settings()

logger = logging.getLogger("app.main")


# --------------------------------------------------
# Rate Limiter
# --------------------------------------------------

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
)


# --------------------------------------------------
# FastAPI App
# --------------------------------------------------

app = FastAPI(
    title="AI Placement Readiness Analyzer API",
    version="1.0.0",
    docs_url="/api/docs"
    if settings.environment == "development"
    else None,
)


# --------------------------------------------------
# Rate Limiter Configuration
# --------------------------------------------------

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

ALLOWED_ORIGINS = [
    # Production Vercel frontend
    "https://ai-placement-resume-analyzer.vercel.app",

    # Local development
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,

    # Allow Vercel preview/deployment URLs as well
    allow_origin_regex=r"https://.*\.vercel\.app",

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Global Exception Handler
# --------------------------------------------------

@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):
    logger.exception(
        "Unhandled exception for %s %s",
        request.method,
        request.url.path,
    )

    if settings.environment == "development":
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc)
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error."
        },
    )


# --------------------------------------------------
# Startup
# --------------------------------------------------

@app.on_event("startup")
async def on_startup():
    await init_indexes()


# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "ai_provider": settings.ai_provider,
    }


# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

app.include_router(auth.router)

app.include_router(resume.router)

app.include_router(jobs.router)

app.include_router(analyze.router)

app.include_router(interview.router)

app.include_router(roadmap.router)

app.include_router(resume_improve.router)

app.include_router(payments.router)

app.include_router(usage.router)

