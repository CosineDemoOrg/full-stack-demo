import logging
import uuid

from sqlmodel import Session, select

from app.core.db import engine, init_db
from app.models import Organization, Membership, User, Item

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    with Session(engine) as session:
        init_db(session)
        # Seed: create 2 orgs + users if not present
        org1 = session.exec(
            select(Organization).where(Organization.name == "Acme Inc.")
        ).first()
        if not org1:
            org1 = Organization(name="Acme Inc.", description="Demo org 1")
            session.add(org1)
            session.commit()
            session.refresh(org1)

        org2 = session.exec(
            select(Organization).where(Organization.name == "Globex Corp.")
        ).first()
        if not org2:
            org2 = Organization(name="Globex Corp.", description="Demo org 2")
            session.add(org2)
            session.commit()
            session.refresh(org2)

        # create demo users if not exist
        user1 = session.exec(
            select(User).where(User.email == "user1@example.com")
        ).first()
        user2 = session.exec(
            select(User).where(User.email == "user2@example.com")
        ).first()
        if not user1:
            # Superuser already created via init_db, create normal users via CRUD? Keeping simple here
            from app.core.security import get_password_hash
            user1 = User(
                email="user1@example.com",
                full_name="User One",
                is_active=True,
                hashed_password=get_password_hash("password123"),
            )
            session.add(user1)
            session.commit()
            session.refresh(user1)
        if not user2:
            from app.core.security import get_password_hash
            user2 = User(
                email="user2@example.com",
                full_name="User Two",
                is_active=True,
                hashed_password=get_password_hash("password123"),
            )
            session.add(user2)
            session.commit()
            session.refresh(user2)

        # memberships
        def ensure_membership(user_id: uuid.UUID, org_id: uuid.UUID, role: str):
            m = session.exec(
                select(Membership).where(
                    (Membership.user_id == user_id) & (Membership.org_id == org_id)
                )
            ).first()
            if not m:
                m = Membership(user_id=user_id, org_id=org_id, role=role)  # type: ignore
                session.add(m)
                session.commit()

        ensure_membership(user1.id, org1.id, "admin")
        ensure_membership(user2.id, org1.id, "member")
        ensure_membership(user2.id, org2.id, "admin")

        # sample items for org1
        existing_items = session.exec(
            select(Item).where(Item.org_id == org1.id)
        ).all()
        if not existing_items:
            item = Item(
                title="Welcome Item",
                description="First item in Acme",
                org_id=org1.id,
                owner_id=user1.id,
            )
            session.add(item)
            session.commit()


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    main()
