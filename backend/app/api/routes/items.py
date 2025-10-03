import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentMembership, CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, membership: CurrentMembership, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items scoped to active org.
    """
    count_statement = (
        select(func.count())
        .select_from(Item)
        .where(Item.org_id == membership.org_id)
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Item)
        .where(Item.org_id == membership.org_id)
        .offset(skip)
        .limit(limit)
    )
    items = session.exec(statement).all()
    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, membership: CurrentMembership, id: uuid.UUID) -> Any:
    """
    Get item by ID within the active org.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.org_id != membership.org_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, membership: CurrentMembership, item_in: ItemCreate
) -> Any:
    """
    Create new item in the active org.
    """
    item = Item.model_validate(item_in, update={"owner_id": current_user.id, "org_id": membership.org_id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    membership: CurrentMembership,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item within the active org.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.org_id != membership.org_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, membership: CurrentMembership, id: uuid.UUID
) -> Message:
    """
    Delete an item within the active org.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.org_id != membership.org_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
