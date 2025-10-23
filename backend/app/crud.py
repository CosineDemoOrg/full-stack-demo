import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, Membership, Organization, Role, User, UserCreate, UserUpdate

def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    # Create a default organization and membership for new users to ensure active_org_id
    org_name = f"Default Org {str(db_obj.id)[:8]}"
    org = Organization(name=org_name)
    session.add(org)
    session.commit()
    session.refresh(org)
    membership = Membership(user_id=db_obj.id, org_id=org.id, role=Role.admin, accepted=True)
    session.add(membership)
    session.commit()
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

def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    # Use the first accepted membership org_id for the owner
    membership = session.exec(
        select(Membership).where((Membership.user_id == owner_id) & (Membership.accepted == True))  # noqa: E712
    ).first()
    if not membership:
        # Create a default org if none exists
        org = Organization(name=f"Default Org {str(owner_id)[:8]}")
        session.add(org)
        session.commit()
        session.refresh(org)
        membership = Membership(user_id=owner_id, org_id=org.id, role=Role.admin, accepted=True)
        session.add(membership)
        session.commit()
        session.refresh(membership)
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id, "org_id": membership.org_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
