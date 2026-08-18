from fastapi import APIRouter, HTTPException, Response, Depends
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError

from app.database import get_db
from app.config import get_settings
from app.models.schemas import SignupRequest, LoginRequest, TokenOut, UserOut
from app.auth.security import hash_password, verify_password, create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()

COOKIE_KWARGS = dict(
    httponly=True,
    secure=settings.environment != "development",
    samesite="lax",
    max_age=settings.jwt_expire_minutes * 60,
    path="/",
)


def _user_out(doc) -> UserOut:
    return UserOut(
        id=str(doc["_id"]),
        name=doc["name"],
        email=doc["email"],
        free_analyses_remaining=doc.get("free_analyses_remaining", 0),
        paid_credits=doc.get("paid_credits", 0),
        created_at=doc["created_at"],
    )


@router.post("/signup", response_model=TokenOut)
async def signup(payload: SignupRequest, response: Response):
    db = get_db()
    doc = {
        "name": payload.name,
        "email": payload.email.lower(),
        "password_hash": hash_password(payload.password),
        "free_analyses_remaining": 0,
        "paid_credits": 0,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = await db.users.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(409, "An account with this email already exists.")

    doc["_id"] = result.inserted_id
    token = create_access_token(str(result.inserted_id))
    response.set_cookie("access_token", token, **COOKIE_KWARGS)
    return TokenOut(access_token=token, user=_user_out(doc))


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginRequest, response: Response):
    db = get_db()
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password.")

    token = create_access_token(str(user["_id"]))
    response.set_cookie("access_token", token, **COOKIE_KWARGS)
    return TokenOut(access_token=token, user=_user_out(user))


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return _user_out(user)
