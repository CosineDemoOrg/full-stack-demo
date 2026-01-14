import random
import string

from fastapi.testclient import TestClient

from app.core.config import settings

def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))

def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"

def get_superuser_token_headers(client: TestClient) -> dict[str, str]:
    login_data = {
        "username": settings.FIRST_SUPERUSER,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    a_token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}

    # Ensure an org exists and switch to it to get active_org_id in token
    org_resp = client.post(f"{settings.API_V1_STR}/orgs/", headers=headers, json={"name": "Admin Org"})
    org_data = org_resp.json()
    org_id = org_data["id"]
    switch_resp = client.post(f"{settings.API_V1_STR}/orgs/switch/{org_id}", headers=headers)
    switched = switch_resp.json()
    a_token = switched["access_token"]
    headers = {"Authorization": f"Bearer {a_token}"}
    return headers
