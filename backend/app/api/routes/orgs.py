import uuid
from typing import Any
from datetime import timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.core import security
from app.models import (
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationsPublic,
    Membership,
    MembershipPublic,
    Token,
)

router = APIRouter(prefix="/orgs", tags=["orgs"])


@router.get("/", response_model=OrganizationsPublic)
def list_my_organizations(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    List organizations the current user is a member of.
    """
    stmt = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    orgs = session.exec(stmt).all()
    count_stmt = (
        select(func.count())
        .select_from(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    count = session.exec(count_stmt).one()
    return OrganizationsPublic(data=orgs, count=count)


@router.post("/", response_model=OrganizationPublic)
def create_organization(session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate) -> Any:
    """
    Create a new organization and assign the creator as admin.
    """
    org = Organization.model_validate(org_in)
    session.add(org)
    session.commit()
    session.refresh(org)

    membership = Membership(user_id=current_user.id, org_id=org.id, role="admin")
    session.add(membership)
    session.commit()
    return org


@router.get("/{org_id}/members", response_model=list[MembershipPublic])
def list_members(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    """
    List members for an organization the user belongs to.
    """
    # verify user belongs
    mem = session.exec(
        select(Membership).where(Membership.user_id == current_user.id, Membership.org_id == org_id)
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    stmt = select(Membership).where(Membership.org_id == org_id)
    members = session.exec(stmt).all()
    return members


@router.post("/switch/{org_id}", response_model=Token)
def switch_active_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Token:
    """
    Switch active organization. Returns a new JWT including active_org_id.
    """
    # verify membership
    mem = session.exec(
        select(Membership).where(Membership.user_id == current_user.id, Membership.org_id == org_id)
    ).first()
    if not mem:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        subject=current_user.id, expires_delta=access_token_expires, extra_claims={"active_org_id": str(org_id)}
    )
    return Token(access_token=token)