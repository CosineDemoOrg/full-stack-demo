import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, TokenDep, require_org_member
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    token: TokenDep,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items scoped by active organization.
    """
    org_id, _ = require_org_member(session, current_user, token)

    count_statement = (
        select(func.count()).select_from(Item).where(Item.org_id == uuid.UUID(org_id))
    )
    count = session.exec(count_statement).one()
    statement = (
        select(Item)
        .where(Item.org_id == uuid.UUID(org_id))
        .offset(skip)
        .limit(limit)
    )

    # Non-admins can only see their own items in the org
    items = session.exec(statement).all()
    if not current_user.is_superuser:
        items = [item for item in items if item.owner_id == current_user.id]

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(
    session: SessionDep, current_user: CurrentUser, token: TokenDep, id: uuid.UUID
) -> Any:
    """
    Get item by ID scoped by active organization.
    """
    org_id, _ = require_org_member(session, current_user, token)
    item = session.get(Item, id)
    if not item or str(item.org_id) != org_id:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    token: TokenDep,
    item_in: ItemCreate,
) -> Any:
    """
    Create new item in active organization.
    """
    org_id, _ = require_org_member(session, current_user, token)
    item = Item.model_validate(
        item_in, update={"owner_id": current_user.id, "org_id": uuid.UUID(org_id)}
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    token: TokenDep,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item in active organization.
    """
    org_id, _ = require_org_member(session, current_user, token)
    item = session.get(Item, id)
    if not item or str(item.org_id) != org_id:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, token: TokenDep, id: uuid.UUID
) -> Message:
    """
    Delete an item in active organization.
    """
    org_id, _ = require_org_member(session, current_user, token)
    item = session.get(Item, id)
    if not item or str(item.org_id) != org_id:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
