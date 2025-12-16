import uuid
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentMembership, CurrentUser, SessionDep
from app.core import security
from app.core.config import settings
from app.models import (
    Membership,
    MembershipCreate,
    MembershipPublic,
    MembershipRole,
    MembershipsPublic,
    Organization,
    OrganizationCreate,
    OrganizationPublic,
    OrganizationUpdate,
    OrganizationsPublic,
    Token,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/", response_model=OrganizationsPublic)
def read_organizations(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    List organizations the current user is a member of.
    """
    membership_statement = select(Membership.org_id).where(
        Membership.user_id == current_user.id
    )
    org_ids = [row[0] for row in session.exec(membership_statement).all()]
    if not org_ids:
        return OrganizationsPublic(data=[], count=0)
    count_statement = (
        select(func.count())
        .select_from(Organization)
        .where(Organization.id.in_(org_ids))
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Organization)
        .where(Organization.id.in_(org_ids))
        .offset(skip)
        .limit(limit)
    )
    orgs = session.exec(statement).all()
    return OrganizationsPublic(data=orgs, count=count)


@router.post("/", response_model=OrganizationPublic)
def create_organization(
    session: SessionDep, current_user: CurrentUser, org_in: OrganizationCreate
) -> Any:
    """
    Create a new organization and add current user as admin member.
    """
    org = Organization.model_validate(org_in)
    session.add(org)
    session.commit()
    session.refresh(org)

    membership = Membership(
        user_id=current_user.id,
        org_id=org.id,
        role=MembershipRole.ADMIN,
    )
    session.add(membership)
    session.commit()
    return org


@router.get("/{org_id}", response_model=OrganizationPublic)
def read_organization(
    session: SessionDep, current_membership: CurrentMembership, org_id: uuid.UUID
) -> Any:
    """
    Get organization details for an org the user is member of.
    """
    org = session.get(Organization, org_id)
    if not org or org.id != current_membership.org_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationPublic)
def update_organization(
    session: SessionDep,
    current_membership: CurrentMembership,
    org_id: uuid.UUID,
    org_in: OrganizationUpdate,
) -> Any:
    """
    Update an organization. Only admins can update.
    """
    if current_membership.role != MembershipRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    org = session.get(Organization, org_id)
    if not org or org.id != current_membership.org_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    update_data = org_in.model_dump(exclude_unset=True)
    org.sqlmodel_update(update_data)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


@router.delete("/{org_id}")
def delete_organization(
    session: SessionDep, current_membership: CurrentMembership, org_id: uuid.UUID
) -> Token:
    """
    Delete an organization. Only admins can delete.
    Returns a token without active_org_id so the user can select another org.
    """
    if current_membership.role != MembershipRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    org = session.get(Organization, org_id)
    if not org or org.id != current_membership.org_id:
        raise HTTPException(status_code=404, detail="Organization not found")

    session.delete(org)
    session.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        subject=current_membership.user_id,
        expires_delta=access_token_expires,
        active_org_id=None,
    )
    return Token(access_token=token)


@router.get("/{org_id}/members", response_model=MembershipsPublic)
def read_members(
    session: SessionDep, current_membership: CurrentMembership, org_id: uuid.UUID
) -> Any:
    """
    List organization members. Requires membership in the organization.
    """
    if org_id != current_membership.org_id:
        raise HTTPException(status_code=404, detail="Organization not found")
    statement = select(Membership).where(Membership.org_id == org_id)
    memberships = session.exec(statement).all()
    return MembershipsPublic(data=memberships, count=len(memberships))


@router.post("/{org_id}/members", response_model=MembershipPublic)
def add_member(
    session: SessionDep,
    current_membership: CurrentMembership,
    org_id: uuid.UUID,
    membership_in: MembershipCreate,
) -> Any:
    """
    Add a member to the organization. Only admins can invite.
    """
    if current_membership.role != MembershipRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if membership_in.org_id != org_id:
        raise HTTPException(status_code=400, detail="Organization mismatch")
    existing = session.get(
        Membership, (membership_in.user_id, membership_in.org_id)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Membership already exists")
    membership = Membership.model_validate(membership_in)
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


@router.delete("/{org_id}/members/{user_id}")
def remove_member(
    session: SessionDep,
    current_membership: CurrentMembership,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Any:
    """
    Remove a member from the organization. Only admins can remove.
    """
    if current_membership.role != MembershipRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    membership = session.get(Membership, (user_id, org_id))
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
    session.delete(membership)
    session.commit()
    return {"message": "Member removed successfully"}


@router.post("/{org_id}/switch", response_model=Token)
def switch_active_organization(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
) -> Token:
    """
    Switch the active organization for the current user by issuing a new JWT.
    """
    membership = session.get(Membership, (current_user.id, org_id))
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="User is not a member of the target organization",
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(
        subject=current_user.id,
        expires_delta=access_token_expires,
        active_org_id=str(org_id),
    )
    return Token(access_token=token)