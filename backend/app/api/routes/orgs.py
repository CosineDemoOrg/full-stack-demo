import uuid
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentMembership, CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import (
    Membership,
    MembershipPublic,
    MembershipsPublic,
    Organization,
    OrganizationPublic,
    OrganizationsPublic,
    RoleEnum,
    Token,
)

router = APIRouter(prefix="/orgs", tags=["orgs"])


@router.get("/", response_model=OrganizationsPublic)
def list_my_orgs(session: SessionDep, current_user: CurrentUser) -> Any:
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id, Membership.is_active == True)  # noqa: E712
    )
    data = session.exec(statement).all()
    count = len(data)
    return OrganizationsPublic(data=data, count=count)


@router.post("/", response_model=OrganizationPublic)
def create_org(session: SessionDep, current_user: CurrentUser, org: OrganizationPublic) -> Any:
    # Create org and set current user as admin member
    new_org = Organization.model_validate(org)
    session.add(new_org)
    session.commit()
    session.refresh(new_org)

    membership = Membership(user_id=current_user.id, org_id=new_org.id, role=RoleEnum.admin, is_active=True)
    session.add(membership)
    session.commit()
    return new_org


@router.post("/{org_id}/switch", response_model=Token)
def switch_active_org(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
) -> Any:
    # verify membership exists and active
    membership = session.exec(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.org_id == org_id,
            Membership.is_active == True,  # noqa: E712
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    access_token = security.create_access_token(
        current_user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        active_org_id=str(org_id),
    )
    return Token(access_token=access_token)


@router.get("/{org_id}/members", response_model=MembershipsPublic)
def list_members(session: SessionDep, current_user: CurrentUser, membership: CurrentMembership, org_id: uuid.UUID) -> Any:
    if membership.org_id != org_id:
        raise HTTPException(status_code=403, detail="Wrong active org")
    data = session.exec(select(Membership).where(Membership.org_id == org_id)).all()
    return MembershipsPublic(data=data, count=len(data))


@router.post("/{org_id}/members", response_model=MembershipPublic)
def add_member(
    session: SessionDep,
    current_user: CurrentUser,
    membership: CurrentMembership,
    org_id: uuid.UUID,
    new_member: MembershipPublic,
) -> Any:
    # Only admins can invite
    if membership.role != RoleEnum.admin or membership.org_id != org_id:
        raise HTTPException(status_code=403, detail="Only admins can invite members")
    # create pending membership (is_active controls acceptance)
    db_member = Membership(
        user_id=new_member.user_id, org_id=org_id, role=new_member.role or RoleEnum.member, is_active=False
    )
    session.add(db_member)
    session.commit()
    session.refresh(db_member)
    return db_member


@router.post("/{org_id}/members/{membership_id}/accept", response_model=MembershipPublic)
def accept_invite(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
) -> Any:
    # user can accept their own pending invite
    m = session.get(Membership, membership_id)
    if not m or m.org_id != org_id:
        raise HTTPException(status_code=404, detail="Invite not found")
    if m.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot accept invite for other user")
    m.is_active = True
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


@router.delete("/{org_id}/members/{membership_id}")
def remove_member(
    session: SessionDep,
    current_user: CurrentUser,
    membership: CurrentMembership,
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
):
    # Only admins can remove
    if membership.role != RoleEnum.admin or membership.org_id != org_id:
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    m = session.get(Membership, membership_id)
    if not m or m.org_id != org_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    session.delete(m)
    session.commit()
    return {"message": "Member removed"}