import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, TokenDep, ensure_admin, ensure_membership, get_active_org_id
from app.core import security
from app.core.config import settings
from app.models import (
    Message,
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationsPublic,
    OrganizationUpdate,
    Token,
)

router = APIRouter(prefix="/orgs", tags=["orgs"])


@router.get("/", response_model=OrganizationsPublic)
def list_orgs(session: SessionDep, current_user: CurrentUser) -> Any:
    statement = (
        select(Organization)
        .join(Organization.memberships)
        .where(Organization.memberships.any(user_id=current_user.id))  # type: ignore
    )
    orgs = session.exec(statement).all()
    count_statement = (
        select(func.count())
        .select_from(Organization)
        .where(Organization.memberships.any(user_id=current_user.id))  # type: ignore
    )
    count = session.exec(count_statement).one()
    return OrganizationsPublic(data=orgs, count=count)


@router.post("/", response_model=OrganizationPublic)
def create_org(session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate) -> Any:
    org = Organization.model_validate(org_in)
    session.add(org)
    session.commit()
    session.refresh(org)
    # Add creator as admin
    from app.models import Membership, Role
    membership = Membership(user_id=current_user.id, org_id=org.id, role=Role.admin)
    session.add(membership)
    session.commit()
    return org


@router.patch("/{org_id}", response_model=OrganizationPublic)
def update_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID, org_in: OrganizationUpdate) -> Any:
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    membership = ensure_membership(session, current_user, org_id)
    ensure_admin(membership)
    update_dict = org_in.model_dump(exclude_unset=True)
    org.sqlmodel_update(update_dict)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


@router.post("/switch/{org_id}", response_model=Token)
def switch_active_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    membership = ensure_membership(session, current_user, org_id)
    expires_delta = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    token = security.create_access_token(
        {"sub": str(current_user.id), "active_org_id": str(org_id)},
        expires_delta=expires_delta,
    )
    return Token(access_token=token)