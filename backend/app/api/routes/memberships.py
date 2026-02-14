import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, ensure_membership
from app.models import (
    Membership,
    MembershipCreate,
    MembershipPublic,
    MembershipUpdate,
    Message,
)

router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.post("/{org_id}", response_model=MembershipPublic)
def invite_member(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
    body: MembershipCreate,
) -> Any:
    """
    Invite/add a user to org (admin only).
    """
    membership = ensure_membership(session, str(current_user.id), str(org_id))
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invite members")
    # prevent duplicates
    existing = session.exec(
        select(Membership).where(
            (Membership.org_id == org_id) & (Membership.user_id == body.user_id)
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User already a member")
    new_member = Membership(user_id=body.user_id, org_id=org_id, role=body.role)
    session.add(new_member)
    session.commit()
    session.refresh(new_member)
    return MembershipPublic.model_validate(new_member)


@router.patch("/{membership_id}", response_model=MembershipPublic)
def update_member_role(
    session: SessionDep,
    current_user: CurrentUser,
    membership_id: uuid.UUID,
    body: MembershipUpdate,
) -> Any:
    """
    Update member role (admin only).
    """
    member = session.get(Membership, membership_id)
    if not member:
        raise HTTPException(status_code=404, detail="Membership not found")
    membership = ensure_membership(session, str(current_user.id), str(member.org_id))
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update roles")
    update_dict = body.model_dump(exclude_unset=True)
    member.sqlmodel_update(update_dict)
    session.add(member)
    session.commit()
    session.refresh(member)
    return MembershipPublic.model_validate(member)


@router.delete("/{membership_id}")
def remove_member(
    session: SessionDep, current_user: CurrentUser, membership_id: uuid.UUID
) -> Message:
    """
    Remove a member (admin only).
    """
    member = session.get(Membership, membership_id)
    if not member:
        raise HTTPException(status_code=404, detail="Membership not found")
    membership = ensure_membership(session, str(current_user.id), str(member.org_id))
    if membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    session.delete(member)
    session.commit()
    return Message(message="Member removed successfully")