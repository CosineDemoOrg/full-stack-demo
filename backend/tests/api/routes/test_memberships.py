import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Organization, Membership, User
from tests.utils.user import authentication_token_from_email


def test_invite_requires_admin(client: TestClient, db: Session) -> None:
    # Setup org and users
    admin_email = "admin_invite@example.com"
    member_email = "member_invite@example.com"
    admin_headers = authentication_token_from_email(client=client, email=admin_email, db=db)
    member_headers = authentication_token_from_email(client=client, email=member_email, db=db)

    org = db.exec(select(Organization).where(Organization.name == "Invite Org")).first()
    if not org:
        org = Organization(name="Invite Org")
        db.add(org)
        db.commit()
        db.refresh(org)

    admin_user = db.exec(select(User).where(User.email == admin_email)).first()
    member_user = db.exec(select(User).where(User.email == member_email)).first()

    db.add(Membership(user_id=admin_user.id, org_id=org.id, role="admin"))
    db.add(Membership(user_id=member_user.id, org_id=org.id, role="member"))
    db.commit()

    # Member cannot invite
    res = client.post(
        f"{settings.API_V1_STR}/orgs/{org.id}/members/invite",
        headers=member_headers,
        params={"org_id": str(org.id), "user_id": str(member_user.id)},
    )
    assert res.status_code == 403

    # Admin can invite a new user
    new_email = "newuser@example.com"
    new_headers = authentication_token_from_email(client=client, email=new_email, db=db)
    new_user = db.exec(select(User).where(User.email == new_email)).first()
    res2 = client.post(
        f"{settings.API_V1_STR}/orgs/{org.id}/members/invite",
        headers=admin_headers,
        params={"org_id": str(org.id), "user_id": str(new_user.id)},
    )
    assert res2.status_code == 200
    mem = res2.json()
    assert mem["user_id"] == str(new_user.id)
    assert mem["org_id"] == str(org.id)
    assert mem["role"] == "member"


def test_remove_requires_admin(client: TestClient, db: Session) -> None:
    # Setup org and users
    admin_email = "admin_remove@example.com"
    victim_email = "victim_remove@example.com"
    admin_headers = authentication_token_from_email(client=client, email=admin_email, db=db)
    victim_headers = authentication_token_from_email(client=client, email=victim_email, db=db)

    org = db.exec(select(Organization).where(Organization.name == "Remove Org")).first()
    if not org:
        org = Organization(name="Remove Org")
        db.add(org)
        db.commit()
        db.refresh(org)

    admin_user = db.exec(select(User).where(User.email == admin_email)).first()
    victim_user = db.exec(select(User).where(User.email == victim_email)).first()

    db.add(Membership(user_id=admin_user.id, org_id=org.id, role="admin"))
    db.add(Membership(user_id=victim_user.id, org_id=org.id, role="member"))
    db.commit()

    # Victim cannot remove admin
    res = client.delete(
        f"{settings.API_V1_STR}/orgs/{org.id}/members/{admin_user.id}",
        headers=victim_headers,
        params={"org_id": str(org.id)},
    )
    assert res.status_code == 403

    # Admin can remove victim
    res2 = client.delete(
        f"{settings.API_V1_STR}/orgs/{org.id}/members/{victim_user.id}",
        headers=admin_headers,
        params={"org_id": str(org.id)},
    )
    assert res2.status_code == 200
    assert res2.json()["message"] == "Member removed"