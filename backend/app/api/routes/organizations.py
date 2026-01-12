import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentMembership, CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import (
    Membership,
    MembershipPublic,
    MembershipsPublic,
    Message,
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationsPublic,
    Token,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/", response_model=OrganizationsPublic)
def read_organizations(
    session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    List organizations the current user belongs to.
    """
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    orgs = session.exec(statement).all()
    count = len(orgs)
    return OrganizationsPublic(data=orgs, count=count)


@router.post("/", response_model=OrganizationPublic)
def create_organization(
    session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate
) -> Any:
    """
    Create a new organization and add the current user as admin.
    """
    org = Organization.model_validate(org_in, update={"owner_id": current_user.id})
    session.add(org)
    session.commit()
    session.refresh(org)

    membership = Membership(user_id=current_user.id, org_id=org.id, role="admin")
    session.add(membership)
    session.commit()

    return org


@router.get("/{org_id}", response_model=OrganizationPublic)
def read_organization(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
) -> Any:
    """
    Get a single organization if the user is a member.
    """
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = session.get(Membership, (current_user.id, org_id))
    if not membership:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return org


@router.get("/{org_id}/members", response_model=MembershipsPublic)
def read_members(
    session: SessionDep,
    current_user: CurrentUser,
    current_membership: CurrentMembership,
    org_id: uuid.UUID,
) -> Any:
    """
    List members of an organization (must belong to it).
    """
    if current_membership.org_id != org_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    statement = select(Membership).where(Membership.org_id == org_id)
    members = session.exec(statement).all()
    count = len(members)
    return MembershipsPublic(data=members, count=count)


@router.post("/{org_id}/members", response_model=MembershipPublic)
def add_member(
    session: SessionDep,
    current_user: CurrentUser,
    current_membership: CurrentMembership,
    org_id: uuid.UUID,
    membership_in: MembershipPublic,
) -> Any:
    """
    Add a member to an organization. Only admins can add.
    """
    if current_membership.org_id != org_id or current_membership.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    existing = session.get(Membership, (membership_in.user_id, org_id))
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    membership = Membership(
        user_id=membership_in.user_id,
        org_id=org_id,
        role=membership_in.role or "member",
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)

    return membership


@router.delete("/{org_id}/members/{user_id}", response_model=Message)
def remove_member(
    session: SessionDep,
    current_user: CurrentUser,
    current_membership: CurrentMembership,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Message:
    """
    Remove a member from an organization. Only admins can remove.
    """
    if current_membership.org_id != org_id or current_membership.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")

    membership = session.get(Membership, (user_id, org_id))
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")

    session.delete(membership)
    session.commit()
    return Message(message="Member removed successfully")


@router.post("/{org_id}/switch", response_model=Token)
def switch_active_org(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
) -> Token:
    """
    Switch the active organization by issuing a new JWT with the selected org.
    """
    membership = session.get(Membership, (current_user.id, org_id))
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of the selected organization",
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        subject=str(current_user.id),
        expires_delta=access_token_expires,
        active_org_id=str(org_id),
    )
    return Token(access_token=token)