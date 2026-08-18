from fastapi import Request, HTTPException, status
from bson import ObjectId
from bson.errors import InvalidId
from app.auth.security import decode_access_token
from app.database import get_db


async def get_current_user(request: Request) -> dict:
    """
    Reads the JWT from the secure HTTP-only cookie (never from a header the
    frontend could forge without also having the cookie). Falls back to
    Authorization header only to make the API testable from tools like curl.
    """
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=401, detail="Invalid session")

    db = get_db()
    user = await db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
