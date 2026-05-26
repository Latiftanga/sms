import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import JWTError, jwt

from app.core.config import settings

_ph = PasswordHasher()


# ── Passwords ─────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ── JWT ───────────────────────────────────────────────────────────

def create_access_token(user_id: str, school_id: str | None, system_role: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "school_id": str(school_id) if school_id else None,
        "role": system_role,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """Raises JWTError on invalid/expired tokens."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ── Document verification tokens (HMAC-SHA256) ────────────────────

def generate_document_token(document_id: str) -> str:
    """Generate an HMAC-signed verification token for a document."""
    nonce = secrets.token_hex(16)
    payload = f"{document_id}:{nonce}"
    sig = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{sig}"


def verify_document_token(token: str) -> str | None:
    """Return document_id if token is valid, else None."""
    try:
        parts = token.rsplit(":", 1)
        if len(parts) != 2:
            return None
        payload, provided_sig = parts
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, provided_sig):
            return None
        document_id = payload.split(":")[0]
        return document_id
    except Exception:
        return None


# ── Invite tokens ─────────────────────────────────────────────────

def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)
