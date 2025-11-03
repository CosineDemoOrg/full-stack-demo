import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ItemCreate,
    Membership,
    MembershipCreate,
    Organization,
    OrganizationCreate,
    OrganizationUpdate,
    User,
    UserCreate,
    UserUpdate,
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(
    *, session: Session, item_in: ItemCreate, owner_id: uuid.UUID, org_id: uuid.UUID
) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id, "org_id": org_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# Organization CRUD
def create_org(*, session: Session, org_in: OrganizationCreate) -> Organization:
    org = Organization.model_validate(org_in)
    session.add(org)
    session.commit()
    session.refresh(org)
    return org


def update_org(*, session: Session, db_org: Organization, org_in: OrganizationUpdate) -> Organization:
    update_dict = org_in.model_dump(exclude_unset=True)
    db_org.sqlmodel_update(update_dict)
    session.add(db_org)
    session.commit()
    session.refresh(db_org)
    return db_org


def list_orgs_for_user(*, session: Session, user_id: uuid.UUID) -> list[Organization]:
    statement = (
        select(Organization)
        .join(Membership, Membership.org_id == Organization.id)
        .where(Membership.user_id == user_id)
    )
    return session.exec(statement).all()


# Membership management
def add_membership(*, session: Session, membership_in: MembershipCreate) -> Membership:
    membership = Membership.model_validate(membership_in)
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def get_membership(*, session: Session, user_id: uuid.UUID, org_id: uuid.UUID) -> Membership | None:
    statement = select(Membership).where(
        Membership.user_id == user_id, Membership.org_id == org_id
    )
    return session.exec(statement).first()


def remove_membership(*, session: Session, membership: Membership) -> None:
    session.delete(membership)
    session.commit()
