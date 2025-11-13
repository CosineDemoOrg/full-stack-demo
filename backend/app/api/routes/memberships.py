import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import Membership, MembershipPublic, User

router = APIRouter(prefix="/orgs/{org_id}/members", tags=["memberships"])


def _require_admin(session: SessionDep, user_id: uuid.UUID, org_id: uuid.UUID) -> None:
    mem = session.exec(
        select(Membership).where(Membership.user_id == user_id, Membership.org_id == org_id)
    ).first()
    if not mem or mem.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")


@router.post("/invite", response_model=MembershipPublic)
def invite_member(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID, user_id: uuid.UUID
) -> Any:
    """
    Invite a user to the organization (admin only).
    """
    _require_admin(session, current_user.id, org_id)

    # verify user exists
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = session.exec(
        select(Membership).where(Membership.user_id == user_id, Membership.org_id == org_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    membership = Membership(user_id=user_id, org_id=org_id, role="member")
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


@router.delete("/{member_user_id}")
def remove_member(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID, member_user_id: uuid.UUID
):
    """
    Remove a user from the organization (admin only).
    """
    _require_admin(session, current_user.id, org_id)

    membership = session.exec(
        select(Membership).where(Membership.user_id == member_user_id, Membership.org_id == org_id)
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    session.delete(membership)
    session.commit()
    return {"message": "Member removed"}