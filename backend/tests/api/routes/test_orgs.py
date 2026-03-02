import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import Role, User


def test_create_org_and_membership(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    data = {"name": "Test Org"}
    response = client.post(f"{settings.API_V1_STR}/orgs/", headers=normal_user_token_headers, json=data)
    assert response.status_code == 200
    org = response.json()
    assert "id" in org and org["name"] == "Test Org"

    # List orgs for user
    response = client.get(f"{settings.API_V1_STR}/orgs/", headers=normal_user_token_headers)
    assert response.status_code == 200
    orgs = response.json()["data"]
    assert any(o["id"] == org["id"] for o in orgs)


def test_invite_requires_admin(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    # Superuser creates org, becomes admin
    data = {"name": "Admin Org"}
    response = client.post(f"{settings.API_V1_STR}/orgs/", headers=superuser_token_headers, json=data)
    assert response.status_code == 200
    org = response.json()

    # Switch org for superuser
    response = client.post(f"{settings.API_V1_STR}/orgs/{org['id']}/switch", headers=superuser_token_headers)
    assert response.status_code == 200
    token = response.json()["access_token"]
    su_headers = {"Authorization": f"Bearer {token}"}

    # Normal user tries to invite in superuser's org without being admin -> forbidden
    invite_body = {"user_id": list(db.query(User).first().__dict__.values())[0], "role": "member"}  # dummy user id
    response = client.post(
        f"{settings.API_V1_STR}/orgs/{org['id']}/invite",
        headers=normal_user_token_headers,
        json=invite_body,
    )
    assert response.status_code in (400, 403)

    # Superuser can invite
    response = client.post(
        f"{settings.API_V1_STR}/orgs/{org['id']}/invite",
        headers=su_headers,
        json={"user_id": list(db.query(User).first().__dict__.values())[0], "role": "member"},
    )
    assert response.status_code == 200