import logging

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Organization, Membership, User
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init() -> None:
    with Session(engine) as session:
        # Ensure superuser exists
        init_db(session)

        # Seed two organizations and users if not present
        org1 = session.exec(
            select(Organization).where(Organization.name == "Acme Corp")
        ).first()
        org2 = session.exec(
            select(Organization).where(Organization.name == "Globex")
        ).first()

        if not org1:
            org1 = Organization(name="Acme Corp")
            session.add(org1)
        if not org2:
            org2 = Organization(name="Globex")
            session.add(org2)
        session.commit()

        # Create two normal users
        user1 = session.exec(select(User).where(User.email == "alice@example.com")).first()
        user2 = session.exec(select(User).where(User.email == "bob@example.com")).first()

        if not user1:
            user1 = User(
                email="alice@example.com",
                full_name="Alice",
                is_active=True,
                hashed_password=get_password_hash("alicepassword"),
            )
            session.add(user1)
        if not user2:
            user2 = User(
                email="bob@example.com",
                full_name="Bob",
                is_active=True,
                hashed_password=get_password_hash("bobpassword"),
            )
            session.add(user2)
        session.commit()

        # Create memberships
        def ensure_membership(u: User, o: Organization, role: str) -> None:
            mem = session.exec(
                select(Membership).where(Membership.user_id == u.id, Membership.org_id == o.id)
            ).first()
            if not mem:
                session.add(Membership(user_id=u.id, org_id=o.id, role=role))

        ensure_membership(user1, org1, "admin")
        ensure_membership(user2, org1, "member")
        ensure_membership(user1, org2, "member")
        ensure_membership(user2, org2, "admin")
        session.commit()

def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")

if __name__ == "__main__":
    main()
