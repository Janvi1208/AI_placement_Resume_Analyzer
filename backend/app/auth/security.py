from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Prefer python-jose when available; otherwise provide a minimal
# HMAC-based fallback compatible with the usage in this project.
try:
    from jose import jwt, JWTError  # type: ignore
except Exception:
    import base64
    import hashlib
    import hmac

    class JWTError(Exception):
        pass

    class _SimpleJWT:
        @staticmethod
        def _b64(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        @staticmethod
        def _unb64(s: str) -> bytes:
            padding = "=" * ((4 - len(s) % 4) % 4)
            return base64.urlsafe_b64decode(s + padding)

        @staticmethod
        def encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
            header = {"alg": algorithm, "typ": "JWT"}
            header_b = _SimpleJWT._b64(json_bytes(header))
            payload_b = _SimpleJWT._b64(json_bytes(payload))
            signing_input = f"{header_b}.{payload_b}".encode()
            sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
            sig_b = _SimpleJWT._b64(sig)
            return f"{header_b}.{payload_b}.{sig_b}"

        @staticmethod
        def decode(token: str, secret: str, algorithms=None) -> dict:
            try:
                header_b, payload_b, sig_b = token.split(".")
                signing_input = f"{header_b}.{payload_b}".encode()
                expected_sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
                sig = _SimpleJWT._unb64(sig_b)
                if not hmac.compare_digest(sig, expected_sig):
                    raise JWTError("Invalid signature")
                payload = json_loads(_SimpleJWT._unb64(payload_b))
                return payload
            except Exception as e:
                raise JWTError(str(e))

    def json_bytes(obj: dict) -> bytes:
        import json

        return json.dumps(obj, separators=(",", ":")).encode()

    def json_loads(b: bytes) -> dict:
        import json

        return json.loads(b.decode())

    jwt = _SimpleJWT()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None
