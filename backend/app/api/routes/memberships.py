import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import ActiveOrgDep, CurrentUser, SessionDep
from app.models import (
    Membership,
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
    MembershipsPublic,
    Organization,
    RoleEnum,
    User,
)

router = APIRouter(prefix="/memberships", tags=["memberships"])


def ensure_admin(session: SessionDep, user_id: uuid.UUID, org_id: uuid.UUID) -> None:
    membership = session.exec(
        select(Membership).where(Membership.user_id == user_id, Membership.org_id == org_id)
    ).first()
    if not membership or membership.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Only admins can perform this action")


@router.get("/org/{org_id}", response_model=MembershipsPublic)
def list_members(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    # only members can list
    membership = session.exec(
        select(Membership).where(Membership.user_id == current_user.id, Membership.org_id == org_id)
    ).first()
    if not membership and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    statement = select(Membership).where(Membership.org_id == org_id)
    members = session.exec(statement).all()
    return MembershipsPublic(data=members, count=len(members))


@router.post("/", response_model=MembershipPublic)
def add_member(session: SessionDep, current_user: CurrentUser, membership_in: MembershipCreate) -> Any:
    # admin check
    ensure_admin(session, current_user.id, membership_in.org_id)
    # verify user and org exist
    if not session.get(User, membership_in.user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if not session.get(Organization, membership_in.org_id):
        raise HTTPException(status_code=404, detail="Organization not found")
    exists = session.exec(
        select(Membership).where(
            Membership.user_id == membership_in.user_id, Membership.org_id == membership_in.org_id
        )
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="User already a member")
    member = Membership.model_validate(membership_in)
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


@router.patch("/{membership_id}", response_model=MembershipPublic)
def update_member(session: SessionDep, current_user: CurrentUser, membership_id: uuid.UUID, membership_in: MembershipUpdate) -> Any:
    db_member = session.get(Membership, membership_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Membership not found")
    ensure_admin(session, current_user.id, db_member.org_id)
    db_member.sqlmodel_update(membership_in.model_dump(exclude_unset=True))
    session.add(db_member)
    session.commit()
    session.refresh(db_member)
    return db_member


@router.delete("/{membership_id}")
def remove_member(session: SessionDep, current_user: CurrentUser, membership_id: uuid.UUID) -> Any:
    db_member = session.get(Membership, membership_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Membership not found")
    ensure_admin(session, current_user.id, db_member.org_id)
    session.delete(db_member)
    session.commit()
    return {"message": "Member removed successfully"}