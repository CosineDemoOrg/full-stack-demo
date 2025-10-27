import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import ActiveOrgDep, CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import (
    Membership,
    MembershipPublic,
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationUpdate,
    OrganizationsPublic,
    RoleEnum,
    Token,
)

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.get("/my", response_model=OrganizationsPublic)
def list_my_orgs(session: SessionDep, current_user: CurrentUser) -> Any:
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    orgs = session.exec(statement).all()
    count = len(orgs)
    return OrganizationsPublic(data=orgs, count=count)


@router.post("/", response_model=OrganizationPublic)
def create_org(session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate) -> Any:
    org = Organization.model_validate(org_in)
    session.add(org)
    session.commit()
    session.refresh(org)
    # add creator as admin member
    member = Membership(user_id=current_user.id, org_id=org.id, role=RoleEnum.admin)
    session.add(member)
    session.commit()
    return org


@router.get("/{org_id}", response_model=OrganizationPublic)
def get_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    # must be a member
    membership = session.exec(
        select(Membership).where(Membership.user_id == current_user.id, Membership.org_id == org_id)
    ).first()
    if not membership and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return org


@router.patch("/{org_id}", response_model=OrganizationPublic)
def update_org(
    session: SessionDep, active_org: ActiveOrgDep, current_user: CurrentUser, org_id: uuid.UUID, org_in: OrganizationUpdate
) -> Any:
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    # require admin
    membership = session.exec(
        select(Membership).where(Membership.user_id == current_user.id, Membership.org_id == org_id)
    ).first()
    if not (current_user.is_superuser or (membership and membership.role == RoleEnum.admin)):
        raise HTTPException(status_code=403, detail="Only admins can update organization")
    update_data = org_in.model_dump(exclude_unset=True)
    org.sqlmodel_update(update_data)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


@router.delete("/{org_id}")
def delete_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    membership = session.exec(
        select(Membership).where(Membership.user_id == current_user.id, Membership.org_id == org_id)
    ).first()
    if not (current_user.is_superuser or (membership and membership.role == RoleEnum.admin)):
        raise HTTPException(status_code=403, detail="Only admins can delete organization")
    session.delete(org)
    session.commit()
    return {"message": "Organization deleted successfully"}


@router.post("/switch/{org_id}", response_model=Token)
def switch_active_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Token:
    # verify membership
    membership = session.exec(
        select(Membership).where(Membership.user_id == current_user.id, Membership.org_id == org_id)
    ).first()
    if not membership and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    access_token = security.create_access_token(
        current_user.id,
        expires_delta=(
            settings.ACCESS_TOKEN_EXPIRE_MINUTES  # type: ignore[arg-type]
        )
        and None,  # will be replaced below
    )
    # The helper expects timedelta, compute it properly
    from datetime import timedelta

    access_token = security.create_access_token(
        current_user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), active_org_id=str(org_id)
    )
    return Token(access_token=access_token)