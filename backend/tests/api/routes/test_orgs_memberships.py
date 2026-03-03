import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import Organization, Membership, OrgRole, User
from tests.utils.user import create_random_user


def test_admin_can_invite_and_remove(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # superuser has default org via init_db
    # list orgs
    r = client.get(f"{settings.API_V1_STR}/orgs/", headers=superuser_token_headers)
    assert r.status_code == 200
    orgs = r.json()["data"]
    assert len(orgs) >= 1
    org_id = orgs[0]["id"]
    # switch token to ensure active_org_id
    token_resp = client.post(
        f"{settings.API_V1_STR}/orgs/{org_id}/switch",
        headers=superuser_token_headers,
    )
    assert token_resp.status_code == 200
    access_token = token_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # invite a user
    new_user = create_random_user(db)
    r2 = client.post(
        f"{settings.API_V1_STR}/memberships/",
        headers=headers,
        json={"user_id": str(new_user.id), "role": "member"},
    )
    assert r2.status_code == 200
    membership = r2.json()
    assert membership["user_id"] == str(new_user.id)
    assert membership["org_id"] == str(org_id)

    # remove
    r3 = client.delete(
        f"{settings.API_V1_STR}/memberships/{membership['id']}", headers=headers
    )
    assert r3.status_code == 200


def test_member_cannot_invite(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # setup: org and two users
    admin = create_random_user(db)
    member = create_random_user(db)
    org = Organization(name="Test Org")
    db.add(org)
    db.commit()
    db.refresh(org)
    db.add(Membership(user_id=admin.id, org_id=org.id, role=OrgRole.admin))
    db.add(Membership(user_id=member.id, org_id=org.id, role=OrgRole.member))
    db.commit()

    # login as member
    from app.core import security
    from datetime import timedelta

    token = security.create_access_token(
        str(member.id),
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        active_org_id=str(org.id),
    )
    headers = {"Authorization": f"Bearer {token}"}
    # attempt invite
    third = create_random_user(db)
    r = client.post(
        f"{settings.API_V1_STR}/memberships/",
        headers=headers,
        json={"user_id": str(third.id), "role": "member"},
    )
    assert r.status_code == 403