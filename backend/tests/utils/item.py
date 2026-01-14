from sqlmodel import Session, select

from app import crud
from app.models import Item, ItemCreate, Organization, Membership
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_item(db: Session) -> Item:
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None

    # Ensure the user has an organization
    org = db.exec(select(Organization).where(Organization.name == "Test Org")).first()
    if not org:
        org = Organization(name="Test Org")
        db.add(org)
        db.commit()
        db.refresh(org)

    mem = db.exec(
        select(Membership).where(Membership.user_id == owner_id, Membership.org_id == org.id)
    ).first()
    if not mem:
        db.add(Membership(user_id=owner_id, org_id=org.id, role="admin"))
        db.commit()

    title = random_lower_string()
    description = random_lower_string()
    item_in = ItemCreate(title=title, description=description)
    return crud.create_item(session=db, item_in=item_in, owner_id=owner_id, org_id=org.id)
