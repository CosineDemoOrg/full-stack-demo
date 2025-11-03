from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"

def create_access_token(subject: str | Any, expires_delta: timedelta | int, active_org_id: str | None = None) -> str:
    # allow passing minutes as int for convenience
    delta = expires_delta if isinstance(expires_delta, timedelta) else timedelta(minutes=expires_delta)
    expire = datetime.now(timezone.utc) + delta
    payload: dict[str, Any] = {"exp": expire, "sub": str(subject)}
    if isinstance(subject, dict):
        # If a dict is provided, merge but ensure exp present
        payload.update({k: v for k, v in subject.items() if k != "exp"})
    if active_org_id:
        payload["active_org_id"] = active_org_id
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
