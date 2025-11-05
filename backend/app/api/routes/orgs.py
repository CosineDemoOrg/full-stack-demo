import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select, col, delete

from app.api.deps import CurrentMembership, CurrentOrg, CurrentUser, SessionDep
from app.models import (
    Membership,
    MembershipCreate,
    MembershipPublic,
    MembershipsPublic,
    Message,
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationsPublic,
    OrganizationUpdate,
)
from app.core import security
from app.core.config import settings

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.get("/", response_model=OrganizationsPublic)
def list_my_orgs(session: SessionDep, current_user: CurrentUser) -> Any:
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    orgs = session.exec(statement).all()
    return OrganizationsPublic(data=orgs, count=len(orgs))


@router.post("/", response_model=OrganizationPublic)
def create_org(
    session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate
) -> Any:
    org = Organization.model_validate(org_in)
    session.add(org)
    session.commit()
    session.refresh(org)
    # add creator as admin
    membership = Membership(user_id=current_user.id, org_id=org.id, role="admin")
    session.add(membership)
    session.commit()
    return org


@router.get("/{org_id}", response_model=OrganizationPublic)
def get_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    # ensure membership
    member_stmt = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org.id
    )
    membership = session.exec(member_stmt).first()
    if not membership and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return org


@router.patch("/{org_id}", response_model=OrganizationPublic)
def update_org(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
    org_in: OrganizationUpdate,
) -> Any:
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    # ensure admin
    member_stmt = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org.id
    )
    membership = session.exec(member_stmt).first()
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update organization")
    org.sqlmodel_update(org_in.model_dump(exclude_unset=True))
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


@router.delete("/{org_id}")
def delete_org(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Message:
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    member_stmt = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org.id
    )
    membership = session.exec(member_stmt).first()
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete organization")
    # cascade will remove related items and memberships
    session.delete(org)
    session.commit()
    return Message(message="Organization deleted successfully")


@router.get("/{org_id}/members", response_model=MembershipsPublic)
def list_members(session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID) -> Any:
    # ensure membership
    member_stmt = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org_id
    )
    membership = session.exec(member_stmt).first()
    if not membership and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    statement = select(Membership).where(Membership.org_id == org_id)
    members = session.exec(statement).all()
    return MembershipsPublic(
        data=[MembershipPublic.model_validate(m) for m in members],
        count=len(members),
    )


@router.post("/{org_id}/members", response_model=MembershipPublic)
def invite_member(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID, body: MembershipCreate
) -> Any:
    # only admin
    admin_stmt = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org_id
    )
    admin = session.exec(admin_stmt).first()
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invite members")
    existing = session.exec(
        select(Membership).where(Membership.user_id == body.user_id, Membership.org_id == org_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already a member")
    membership = Membership(user_id=body.user_id, org_id=org_id, role=body.role or "member")
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


@router.delete("/{org_id}/members/{user_id}")
def remove_member(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID, user_id: uuid.UUID
) -> Message:
    # only admin
    admin_stmt = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org_id
    )
    admin = session.exec(admin_stmt).first()
    if not admin or admin.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove members")
    membership = session.exec(
        select(Membership).where(Membership.user_id == user_id, Membership.org_id == org_id)
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    session.delete(membership)
    session.commit()
    return Message(message="Member removed successfully")


from app.models import Token

@router.post("/{org_id}/switch", response_model=Token)
def switch_active_org(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
) -> Token:
    # ensure membership
    member_stmt = select(Membership).where(
        Membership.user_id == current_user.id, Membership.org_id == org_id
    )
    membership = session.exec(member_stmt).first()
    if not membership and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    # issue a new token with active org
    token = security.create_access_token(
        current_user.id,
        expires_delta=__import__("datetime").timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        active_org_id=str(org_id),
    )
    return Token(access_token=token)