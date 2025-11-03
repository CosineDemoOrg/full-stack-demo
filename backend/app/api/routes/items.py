import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep, ensure_membership, get_active_org_id, TokenDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep, current_user: CurrentUser, token: TokenDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve items scoped by active org.
    """
    active_org_id = get_active_org_id(token)
    if not active_org_id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="No active organization selected")

    if current_user.is_superuser and not active_org_id:
        count_statement = select(func.count()).select_from(Item)
        count = session.exec(count_statement).one()
        statement = select(Item).offset(skip).limit(limit)
        items = session.exec(statement).all()
        return ItemsPublic(data=items, count=count)

    # Ensure membership for non-superusers
    membership = ensure_membership(session, current_user, active_org_id)  # type: ignore

    if membership.role.name == "admin":
        count_statement = (
            select(func.count()).select_from(Item).where(Item.org_id == active_org_id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Item).where(Item.org_id == active_org_id).offset(skip).limit(limit)
        )
        items = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Item)
            .where(Item.org_id == active_org_id, Item.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Item)
            .where(Item.org_id == active_org_id, Item.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        items = session.exec(statement).all()

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, token: TokenDep, id: uuid.UUID) -> Any:
    """
    Get item by ID scoped by active org.
    """
    active_org_id = get_active_org_id(token)
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if active_org_id and item.org_id != active_org_id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Cross-org access denied")
    if not current_user.is_superuser:
        membership = ensure_membership(session, current_user, item.org_id)
        if membership.role.name != "admin" and (item.owner_id != current_user.id):
            raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, token: TokenDep, item_in: ItemCreate
) -> Any:
    """
    Create new item scoped by active org.
    """
    active_org_id = get_active_org_id(token)
    if not active_org_id and not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="No active organization selected")

    # Ensure membership
    ensure_membership(session, current_user, active_org_id)  # type: ignore

    item = Item.model_validate(
        item_in, update={"owner_id": current_user.id, "org_id": active_org_id}  # type: ignore
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
    Update an item scoped by active org.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        membership = ensure_membership(session, current_user, item.org_id)
        if membership.role.name != "admin" and (item.owner_id != current_user.id):
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
    Delete an item scoped by active org.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser:
        membership = ensure_membership(session, current_user, item.org_id)
        if membership.role.name != "admin" and (item.owner_id != current_user.id):
            raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")
