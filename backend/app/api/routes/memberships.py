import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, ensure_admin, ensure_membership
from app.models import (
    Membership,
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
    MembershipsPublic,
    Message,
    Organization,
)

router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.get("/org/{org_id}", response_model=MembershipsPublic)
def list_members(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    membership = ensure_membership(session, current_user, org_id)
    ensure_admin(membership)
    statement = select(Membership).where(Membership.org_id == org_id)
    members = session.exec(statement).all()
    count = session.exec(select(func.count()).select_from(Membership).where(Membership.org_id == org_id)).one()
    return MembershipsPublic(data=members, count=count)


@router.post("/", response_model=MembershipPublic)
def invite_member(session: SessionDep, current_user: CurrentUser, membership_in: MembershipCreate) -> Any:
    # Only admins in the org can invite
    membership = ensure_membership(session, current_user, membership_in.org_id)
    ensure_admin(membership)
    # Validate org exists
    org = session.get(Organization, membership_in.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    new_membership = Membership.model_validate(membership_in)
    session.add(new_membership)
    session.commit()
    session.refresh(new_membership)
    return new_membership


@router.patch("/{membership_id}", response_model=MembershipPublic)
def update_membership(session: SessionDep, current_user: CurrentUser, membership_id: uuid.UUID, membership_in: MembershipUpdate) -> Any:
    membership = session.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    admin_membership = ensure_membership(session, current_user, membership.org_id)
    ensure_admin(admin_membership)
    update_dict = membership_in.model_dump(exclude_unset=True)
    membership.sqlmodel_update(update_dict)
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


@router.delete("/{membership_id}", response_model=Message)
def remove_member(session: SessionDep, current_user: CurrentUser, membership_id: uuid.UUID) -> Message:
    membership = session.get(Membership, membership_id)
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    admin_membership = ensure_membership(session, current_user, membership.org_id)
    ensure_admin(admin_membership)
    session.delete(membership)
    session.commit()
    return Message(message="Member removed")