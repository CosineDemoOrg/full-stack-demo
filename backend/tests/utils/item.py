from sqlmodel import Session

from app import crud
from app.models import Item, ItemCreate, Organization, Membership, OrgRole
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_item(db: Session) -> Item:
    user = create_random_user(db)
    owner_id = user.id
    assert owner_id is not None
    # ensure org and membership
    org = Organization(name=f"Org {random_lower_string()}")
    db.add(org)
    db.commit()
    db.refresh(org)
    membership = Membership(user_id=owner_id, org_id=org.id, role=OrgRole.admin)
    db.add(membership)
    db.commit()

    title = random_lower_string()
    description = random_lower_string()
    item_in = ItemCreate(title=title, description=description)
    return crud.create_item(session=db, item_in=item_in, owner_id=owner_id, org_id=org.id)
