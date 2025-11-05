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
from app.models import Membership, TokenPayload, User, Organization

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
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
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


def get_current_org(session: SessionDep, token: TokenDep, current_user: CurrentUser) -> Organization:
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
    if not token_data.active_org_id:
        raise HTTPException(status_code=400, detail="No active organization in token")
    org = session.get(Organization, token_data.active_org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    # Ensure user has membership in org
    statement = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org.id
    )
    membership = session.exec(statement).first()
    if not membership and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return org


def get_current_membership(
    session: SessionDep, current_user: CurrentUser, current_org: Annotated[Organization, Depends(get_current_org)]
) -> Membership | None:
    statement = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == current_org.id
    )
    membership = session.exec(statement).first()
    return membership


CurrentOrg = Annotated[Organization, Depends(get_current_org)]
CurrentMembership = Annotated[Membership | None, Depends(get_current_membership)]
