from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, delete

from app import models  # ensure models are imported for SQLModel metadata
from app.core.config import settings
from app.core import db as app_db
from app.api import deps as api_deps
from app.models import Item, User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

# Use a local SQLite database file for tests instead of the external Postgres DB
test_engine = create_engine(
    "sqlite:///./test.db",
    connect_args={"check_same_thread": False},
)

# Override the application-wide engine and any modules that imported it directly
app_db.engine = test_engine
api_deps.engine = test_engine

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    # Create all tables in the in-memory SQLite database
    SQLModel.metadata.create_all(app_db.engine)

    with Session(app_db.engine) as session:
        app_db.init_db(session)
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
