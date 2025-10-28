import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import ActiveOrgId, CurrentMembership, CurrentUser, SessionDep
from app.models import (
    Membership,
    MembershipBase,
    MembershipPublic,
    MembershipsPublic,
    OrgRole,
    User,
    Message,
)

router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.get("/", response_model=MembershipsPublic)
def list_memberships(
    session: SessionDep, current_user: CurrentUser, org_id: ActiveOrgId, _: CurrentMembership
) -> Any:
    statement = select(Membership).where(Membership.org_id == org_id)
    memberships = session.exec(statement).all()
    return MembershipsPublic(
        data=[MembershipPublic.model_validate(m) for m in memberships],
        count=len(memberships),
    )


@router.post("/", response_model=MembershipPublic)
def invite_member(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: ActiveOrgId,
    current_membership: CurrentMembership,
    body: MembershipBase & dict[str, Any],
) -> Any:
    # only admin can invite
    if current_membership.role != OrgRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can invite")
    user_id = body.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    exists = session.exec(
        select(Membership).where(Membership.user_id == user_id, Membership.org_id == org_id)
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="User already a member")

    membership = Membership(user_id=user_id, org_id=org_id, role=body.get("role", OrgRole.member))
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return MembershipPublic.model_validate(membership)


@router.delete("/{membership_id}")
def remove_member(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: ActiveOrgId,
    current_membership: CurrentMembership,
    membership_id: uuid.UUID,
) -> Message:
    # only admin can remove
    if current_membership.role != OrgRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can remove")
    membership = session.get(Membership, membership_id)
    if not membership or str(membership.org_id) != org_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    session.delete(membership)
    session.commit()
    return Message(message="Member removed")