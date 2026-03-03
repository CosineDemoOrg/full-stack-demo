import uuid
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import (
    ActiveOrgId,
    CurrentMembership,
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from fastapi import Depends
from app.core import security
from app.core.config import settings
from app.models import (
    Message,
    Organization,
    OrganizationBase,
    OrganizationPublic,
    OrganizationsPublic,
    Membership,
    MembershipPublic,
    OrgRole,
    Token,
)

router = APIRouter(prefix="/orgs", tags=["orgs"])


@router.get("/", response_model=OrganizationsPublic)
def list_orgs(session: SessionDep, current_user: CurrentUser) -> Any:
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == current_user.id)
    )
    orgs = session.exec(statement).all()
    count = len(orgs)
    return OrganizationsPublic(
        data=[OrganizationPublic.model_validate(o) for o in orgs], count=count
    )


@router.post("/", response_model=OrganizationPublic)
def create_org(
    session: SessionDep, current_user: CurrentUser, body: OrganizationBase
) -> Any:
    org = Organization.model_validate(body)
    session.add(org)
    session.commit()
    session.refresh(org)

    # creator becomes admin
    membership = Membership(
        user_id=current_user.id, org_id=org.id, role=OrgRole.admin
    )
    session.add(membership)
    session.commit()
    return OrganizationPublic.model_validate(org)


@router.get("/{org_id}", response_model=OrganizationPublic)
def get_org(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
) -> Any:
    # ensure membership
    membership = session.exec(
        select(Membership).where(
            Membership.user_id == current_user.id, Membership.org_id == org_id
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrganizationPublic.model_validate(org)


@router.delete("/{org_id}")
def delete_org(
    session: SessionDep,
    current_user: CurrentUser,
    org_id: uuid.UUID,
) -> Message:
    # only admin members can delete
    membership = session.exec(
        select(Membership).where(
            Membership.user_id == current_user.id, Membership.org_id == org_id
        )
    ).first()
    if not membership or membership.role != OrgRole.admin:
        raise HTTPException(status_code=403, detail="Only admins can delete org")
    org = session.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    session.delete(org)
    session.commit()
    return Message(message="Organization deleted successfully")


@router.post("/{org_id}/switch", response_model=Token)
def switch_active_org(
    session: SessionDep, current_user: CurrentUser, org_id: uuid.UUID
) -> Token:
    # verify membership
    membership = session.exec(
        select(Membership).where(
            Membership.user_id == current_user.id, Membership.org_id == org_id
        )
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    # mint new token with active_org_id
    return Token(
        access_token=security.create_access_token(
            str(current_user.id),
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            active_org_id=str(org_id),
        )
    )