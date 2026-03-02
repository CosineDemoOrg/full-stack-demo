import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import ActiveOrgDep, CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, active_org: ActiveOrgDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items scoped by active organization.
    """
    if current_user.is_superuser and not active_org.org:
        count_statement = select(func.count()).select_from(Item)
        count = session.exec(count_statement).one()
        statement = select(Item).offset(skip).limit(limit)
        items = session.exec(statement).all()
    else:
        if active_org.org:
            count_statement = (
                select(func.count())
                .select_from(Item)
                .where(Item.org_id == active_org.org.id)
            )
            count = session.exec(count_statement).one()
            statement = (
                select(Item)
                .where(Item.org_id == active_org.org.id)
                .offset(skip)
                .limit(limit)
            )
            items = session.exec(statement).all()
        else:
            # fallback: personal items owned by user without org
            count_statement = (
                select(func.count())
                .select_from(Item)
                .where(Item.owner_id == current_user.id, Item.org_id.is_(None))  # type: ignore
            )
            count = session.exec(count_statement).one()
            statement = (
                select(Item)
                .where(Item.owner_id == current_user.id, Item.org_id.is_(None))  # type: ignore
                .offset(skip)
                .limit(limit)
            )
            items = session.exec(statement).all()

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, active_org: ActiveOrgDep, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        if item.org_id is None:
            if item.owner_id != current_user.id:
                raise HTTPException(status_code=400, detail="Not enough permissions")
        else:
            if not active_org.org or item.org_id != active_org.org.id:
                raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, active_org: ActiveOrgDep, item_in: ItemCreate
) -> Any:
    """
    Create new item in active organization.
    """
    if active_org.org:
        item = Item.model_validate(item_in, update={"owner_id": current_user.id, "org_id": active_org.org.id})
    else:
        item = Item.model_validate(item_in, update={"owner_id": current_user.id})
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.put("/{id}", response_model=ItemPublic)
def update_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    active_org: ActiveOrgDep,
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        if item.org_id is None:
            if item.owner_id != current_user.id:
                raise HTTPException(status_code=400, detail="Not enough permissions")
        else:
            if not active_org.org or item.org_id != active_org.org.id:
                raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = item_in.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.delete("/{id}")
def delete_item(
    session: SessionDep, current_user: CurrentUser, active_org: ActiveOrgDep, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        if item.org_id is None:
            if item.owner_id != current_user.id:
                raise HTTPException(status_code=400, detail="Not enough permissions")
        else:
            if not active_org.org or item.org_id != active_org.org.id:
                raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
