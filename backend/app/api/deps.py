from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import Membership, TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]

def get_token_payload(token: TokenDep) -> TokenPayload:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    return token_data

def get_current_user(session: SessionDep, token: TokenDep) -> User:
    token_data = get_token_payload(token)
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def get_active_org_id(token: TokenDep) -> str:
    token_data = get_token_payload(token)
    if not token_data.active_org_id:
        raise HTTPException(
            status_code=400, detail="Active organization not set in token"
        )
    return token_data.active_org_id

def ensure_membership(session: SessionDep, user_id: str, org_id: str) -> Membership:
    statement = select(Membership).where(
        (Membership.user_id == user_id) & (Membership.org_id == org_id)
    )
    membership = session.exec(statement).first()
    if not membership:
        raise HTTPException(status_code=403, detail="User is not a member of this organization")
    return membership


CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
