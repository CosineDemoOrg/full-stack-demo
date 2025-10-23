from collections.abc import Generator
from typing import Annotated, Tuple
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import Membership, Role, TokenPayload, User

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

def get_active_org_id(token: TokenDep) -> str | None:
    token_data = get_token_payload(token)
    return token_data.active_org_id

def require_org_member(session: SessionDep, current_user: User, token: TokenDep) -> Tuple[str, Membership]:
    org_id = get_active_org_id(token)
    if not org_id:
        raise HTTPException(status_code=400, detail="No active organization selected")
    statement = select(Membership).where(
        (Membership.user_id == current_user.id) & (Membership.org_id == uuid.UUID(org_id))
    )
    membership = session.exec(statement).first()
    if not membership or not membership.accepted:
        raise HTTPException(status_code=403, detail="User is not a member of the active organization")
    return org_id, membership

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

def require_admin(session: SessionDep, current_user: CurrentUser, token: TokenDep) -> Tuple[str, Membership]:
    org_id, membership = require_org_member(session, current_user, token)
    if membership.role != Role.admin:
        raise HTTPException(status_code=403, detail="Only organization admins can perform this action")
    return org_id, membership
