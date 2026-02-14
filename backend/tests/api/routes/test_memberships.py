from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Organization, Membership, User, UserCreate
from tests.utils.user import authentication_token_from_email


def test_invite_requires_admin(client: TestClient, db: Session) -> None:
    # create two users
    u_admin = db.exec(select(User).where(User.email == "role_admin@example.com")).first()
    u_member = db.exec(select(User).where(User.email == "role_member@example.com")).first()
    from app import crud
    if not u_admin:
        u_admin = crud.create_user(session=db, user_create=UserCreate(email="role_admin@example.com", password="password123"))
    if not u_member:
        u_member = crud.create_user(session=db, user_create=UserCreate(email="role_member@example.com", password="password123"))

    # create org and add both, make admin admin, member member
    org = Organization(name="Role Test Org")
    db.add(org)
    db.commit()
    db.refresh(org)
    db.add(Membership(user_id=u_admin.id, org_id=org.id, role="admin"))  # type: ignore
    db.add(Membership(user_id=u_member.id, org_id=org.id, role="member"))  # type: ignore
    db.commit()

    # login as member and try to invite another user
    member_headers = authentication_token_from_email(client=client, email="role_member@example.com", db=db)
    r = client.post(
        f"{settings.API_V1_STR}/memberships/{org.id}",
        headers=member_headers,
        json={"user_id": str(u_admin.id), "role": "member"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Only admins can invite members"