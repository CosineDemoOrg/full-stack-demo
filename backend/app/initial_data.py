import logging

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Organization, Membership, OrgRole, User, UserCreate
from app import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        # Seed: create 2 orgs + users if not present
        # Org A
        org_a = Organization(name="Acme Inc")
        session.add(org_a)
        session.commit()
        session.refresh(org_a)

        # Org B
        org_b = Organization(name="Globex Corp")
        session.add(org_b)
        session.commit()
        session.refresh(org_b)

        # Users
        def get_or_create_user(email: str, full_name: str) -> User:
            existing = crud.get_user_by_email(session=session, email=email)
            if existing:
                return existing
            return crud.create_user(
                session=session,
                user_create=UserCreate(
                    email=email, password="password123", full_name=full_name
                ),
            )

        alice = get_or_create_user("alice@example.com", "Alice")
        bob = get_or_create_user("bob@example.com", "Bob")
        charlie = get_or_create_user("charlie@example.com", "Charlie")

        # memberships
        session.add_all(
            [
                Membership(user_id=alice.id, org_id=org_a.id, role=OrgRole.admin),
                Membership(user_id=bob.id, org_id=org_a.id, role=OrgRole.member),
                Membership(user_id=charlie.id, org_id=org_b.id, role=OrgRole.admin),
            ]
        )
        session.commit()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
