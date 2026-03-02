#!/usr/bin/env python3
import logging
import uuid

from sqlmodel import Session, select

from app.core.db import engine
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Organization, Membership, Role, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_or_create_user(session: Session, email: str, password: str, full_name: str | None = None, is_superuser: bool = False) -> User:
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        return user
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name=full_name,
        is_superuser=is_superuser,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_or_create_org(session: Session, name: str) -> Organization:
    org = session.exec(select(Organization).where(Organization.name == name)).first()
    if org:
        return org
    org = Organization(name=name)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def ensure_membership(session: Session, user: User, org: Organization, role: Role) -> Membership:
    m = session.exec(
        select(Membership).where((Membership.user_id == user.id) & (Membership.org_id == org.id))
    ).first()
    if m:
        return m
    m = Membership(user_id=user.id, org_id=org.id, role=role, accepted=True)
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


def main() -> None:
    logger.info("Seeding organizations and users")
    with Session(engine) as session:
        # Superuser from settings
        superuser = get_or_create_user(
            session=session,
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )

        # Additional users
        alice = get_or_create_user(session, "alice@example.com", "alicepassword", full_name="Alice")
        bob = get_or_create_user(session, "bob@example.com", "bobpassword", full_name="Bob")

        # Orgs
        org_acme = get_or_create_org(session, "Acme Inc")
        org_umbrella = get_or_create_org(session, "Umbrella Corp")

        # Memberships
        ensure_membership(session, superuser, org_acme, Role.admin)
        ensure_membership(session, alice, org_acme, Role.member)

        ensure_membership(session, superuser, org_umbrella, Role.admin)
        ensure_membership(session, bob, org_umbrella, Role.member)

    logger.info("Seeding done")


if __name__ == "__main__":
    main()