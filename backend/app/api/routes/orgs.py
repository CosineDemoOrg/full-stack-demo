import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, get_active_org_id, ensure_membership
from app.core import security
from app.core.config import settings
from app.models import (
    Message,
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationUpdate,
    OrganizationsPublic,
    Membership,
    MembershipPublic,
)
from datetime import timedelta

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.get("/", response_model=OrganizationsPublic)
def list_orgs(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    List organizations current user belongs to.
    """
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    orgs = session.exec(statement).all()
    count = len(orgs)
    return OrganizationsPublic(
        data=[OrganizationPublic.model_validate(o) for o in orgs], count=count
    )


@router.post("/", response_model=OrganizationPublic)
def create_org(
    session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate
) -> Any:
    """
    Create a new organization and add current user as admin.
    """
    db_org = Organization.model_validate(org_in)
    session.add(db_org)
    session.commit()
    session.refresh(db_org)
    membership = Membership(
        user_id=current_user.id, org_id=db_org.id, role="admin"  # type: ignore
    )
    session.add(membership)
    session.commit()
    return OrganizationPublic.model_validate(db_org)


@router.patch("/{org_id}", response_model=OrganizationPublic)
def update_org(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
    org_in: OrganizationUpdate,
) -> Any:
    """
    Update an organization (admin only).
    """
    membership = ensure_membership(session, str(current_user.id), str(org_id))
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update organization")
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    update_dict = org_in.model_dump(exclude_unset=True)
    org.sqlmodel_update(update_dict)
    session.add(org)
    session.commit()
    session.refresh(org)
    return OrganizationPublic.model_validate(org)


@router.delete("/{org_id}")
def delete_org(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
) -> Message:
    """
    Delete an organization (admin only).
    """
    membership = ensure_membership(session, str(current_user.id), str(org_id))
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete organization")
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    session.delete(org)
    session.commit()
    return Message(message="Organization deleted successfully")


@router.post("/switch/{org_id}")
def switch_active_org(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
):
    """
    Switch active organization by issuing a new JWT including active_org_id.
    """
    ensure_membership(session, str(current_user.id), str(org_id))
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        current_user.id, expires_delta=access_token_expires, active_org_id=str(org_id)
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/{org_id}/members", response_model=list[MembershipPublic])
def list_members(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
) -> Any:
    """
    List members of an organization.
    """
    ensure_membership(session, str(current_user.id), str(org_id))
    statement = select(Membership).where(Membership.org_id == org_id)
    members = session.exec(statement).all()
    return [MembershipPublic.model_validate(m) for m in members]