import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, get_active_org_id, ensure_membership
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    active_org_id: str = Depends(get_active_org_id),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve items scoped to active organization.
    """
    ensure_membership(session, str(current_user.id), active_org_id)

    count_statement = (
        select(func.count())
        .select_from(Item)
        .where(Item.org_id == uuid.UUID(active_org_id))
    )
    count = session.exec(count_statement).one()

    if current_user.is_superuser:
        statement = (
            select(Item)
            .where(Item.org_id == uuid.UUID(active_org_id))
            .offset(skip)
            .limit(limit)
        )
    else:
        statement = (
            select(Item)
            .where(
                (Item.org_id == uuid.UUID(active_org_id))
                & (Item.owner_id == current_user.id)
            )
            .offset(skip)
            .limit(limit)
        )
    items = session.exec(statement).all()

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(
    session: SessionDep,
    current_user: CurrentUser,
    active_org_id: str = Depends(get_active_org_id),
    id: uuid.UUID,
) -> Any:
    """
    Get item by ID.
    """
    ensure_membership(session, str(current_user.id), active_org_id)
    item = session.get(Item, id)
    if not item or str(item.org_id) != active_org_id:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    active_org_id: str = Depends(get_active_org_id),
    item_in: ItemCreate,
) -> Any:
    """
    Create new item in active organization.
    """
    ensure_membership(session, str(current_user.id), active_org_id)
    item = Item.model_validate(
        item_in, update={"owner_id": current_user.id, "org_id": uuid.UUID(active_org_id)}
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
    active_org_id: str = Depends(get_active_org_id),
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    ensure_membership(session, str(current_user.id), active_org_id)
    item = session.get(Item, id)
    if not item or str(item.org_id) != active_org_id:
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
    session: SessionDep,
    current_user: CurrentUser,
    active_org_id: str = Depends(get_active_org_id),
    id: uuid.UUID,
) -> Message:
    """
    Delete an item.
    """
    ensure_membership(session, str(current_user.id), active_org_id)
    item = session.get(Item, id)
    if not item or str(item.org_id) != active_org_id:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
