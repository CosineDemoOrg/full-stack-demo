import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Organization, Membership, Role, User
from app.core.security import create_access_token

def get_token_for_user(session: Session, user: User, org: Organization | None = None) -> dict[str, str]:
    token = create_access_token(subject=str(user.id), expires_delta=1, active_org_id=str(org.id) if org else None)
    return {"Authorization": f"Bearer {token}"}

def test_invite_requires_admin(client: TestClient, db: Session) -> None:
    # Setup: create org and two users, make one member (non-admin)
    user_admin = db.exec(select(User).where(User.email == "alice@example.com")).first()
    user_member = db.exec(select(User).where(User.email == "bob@example.com")).first()
    org = db.exec(select(Organization).where(Organization.name == "Org A")).first()
    assert user_admin and user_member and org

    # Ensure bob is member but not admin in Org A
    membership = db.exec(select(Membership).where(Membership.user_id == user_member.id, Membership.org_id == org.id)).first()
    assert membership and membership.role == Role.member

    member_token_headers = get_token_for_user(db, user_member, org)
    payload = {"user_id": str(user_admin.id), "org_id": str(org.id), "role": "member"}
    response = client.post(f"{settings.API_V1_STR}/memberships/", headers=member_token_headers, json=payload)
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin privileges required"