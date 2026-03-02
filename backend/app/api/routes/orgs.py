import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app.api.deps import (
    CurrentUser,
    SessionDep,
    TokenDep,
    get_active_org_id,
    require_admin,
    require_org_member,
)
from app.core import security
from app.core.config import settings
from app.models import (
    Membership,
    MembershipCreate,
    MembershipPublic,
    MembershipsPublic,
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationsPublic,
    Role,
    Token,
)

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.get("/", response_model=OrganizationsPublic)
def list_my_orgs(session: SessionDep, current_user: CurrentUser) -> Any:
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    orgs = session.exec(statement).all()
    count = len(orgs)
    return OrganizationsPublic(
        data=[OrganizationPublic(id=o.id, name=o.name) for o in orgs], count=count
    )


@router.post("/", response_model=OrganizationPublic)
def create_org(
    session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate
) -> Any:
    org = Organization.model_validate(org_in)
    session.add(org)
    session.commit()
    session.refresh(org)
    # make current user admin member
    membership = Membership(
        user_id=current_user.id, org_id=org.id, role=Role.admin, accepted=True
    )
    session.add(membership)
    session.commit()
    return OrganizationPublic(id=org.id, name=org.name)


@router.post("/{org_id}/switch", response_model=Token)
def switch_active_org(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
) -> Any:
    # verify membership exists
    statement = select(Membership).where(
        (Membership.user_id == current_user.id) & (Membership.org_id == org_id)
    )
    membership = session.exec(statement).first()
    if not membership or not membership.accepted:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    access_token = security.create_access_token(
        current_user.id,
        expires_delta=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # minutes already
        active_org_id=str(org_id),
    )
    # return new token to be used by client
    return Token(access_token=access_token)


@router.get("/{org_id}/members", response_model=MembershipsPublic)
def list_members(
    session: SessionDep, current_user: CurrentUser, token: TokenDep, org_id: uuid.UUID
) -> Any:
    # Verify requester is member of org
    active_org_id, _ = require_org_member(session, current_user, token)
    if str(org_id) != active_org_id:
        raise HTTPException(status_code=400, detail="Active org mismatch")
    stmt = select(Membership).where(Membership.org_id == org_id)
    members = session.exec(stmt).all()
    return MembershipsPublic(
        data=[
            MembershipPublic(
                id=m.id, user_id=m.user_id, org_id=m.org_id, role=m.role, accepted=m.accepted
            )
            for m in members
        ],
        count=len(members),
    )


@router.post("/{org_id}/invite", response_model=MembershipPublic)
def invite_member(
    session: SessionDep,
    current_user: CurrentUser,
    token: TokenDep,
    org_id: uuid.UUID,
    body: MembershipCreate,
) -> Any:
    # Only admins can invite
    active_org_id, _ = require_admin(session, current_user, token)
    if str(org_id) != active_org_id:
        raise HTTPException(status_code=400, detail="Active org mismatch")
    # Create pending membership for existing user
    m = Membership(user_id=body.user_id, org_id=org_id, role=body.role, accepted=False)
    session.add(m)
    session.commit()
    session.refresh(m)
    return MembershipPublic(
        id=m.id, user_id=m.user_id, org_id=m.org_id, role=m.role, accepted=m.accepted
    )


@router.post("/{org_id}/members/{membership_id}/accept", response_model=MembershipPublic)
def accept_invite(
    session: SessionDep,
    current_user: CurrentUser,
    token: TokenDep,
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
) -> Any:
    active_org_id, _ = require_org_member(session, current_user, token)
    if str(org_id) != active_org_id:
        raise HTTPException(status_code=400, detail="Active org mismatch")
    m = session.get(Membership, membership_id)
    if not m or m.org_id != org_id or m.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Invitation not found")
    m.accepted = True
    session.add(m)
    session.commit()
    session.refresh(m)
    return MembershipPublic(
        id=m.id, user_id=m.user_id, org_id=m.org_id, role=m.role, accepted=m.accepted
    )


@router.delete("/{org_id}/members/{membership_id}")
def remove_member(
    session: SessionDep,
    current_user: CurrentUser,
    token: TokenDep,
    org_id: uuid.UUID,
    membership_id: uuid.UUID,
):
    active_org_id, _ = require_admin(session, current_user, token)
    if str(org_id) != active_org_id:
        raise HTTPException(status_code=400, detail="Active org mismatch")
    m = session.get(Membership, membership_id)
    if not m or m.org_id != org_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    session.delete(m)
    session.commit()
    return {"message": "Member removed"}