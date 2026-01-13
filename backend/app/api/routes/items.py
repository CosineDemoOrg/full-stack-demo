import csv
import io
import uuid
from typing import Any, Iterable

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import Item, ItemCreate, ItemPublic, ItemsPublic, ItemUpdate, Message

router = APIRouter(prefix="/items", tags=["items"])


def _iter_items_for_user(
    session: SessionDep, current_user: CurrentUser, *, search: str | None = None
) -> Iterable[Item]:
    if current_user.is_superuser:
        statement = select(Item)
    else:
        statement = select(Item).where(Item.owner_id == current_user.id)
    if search:
        statement = statement.where(Item.title.contains(search))
    return session.exec(statement)


@router.get("/", response_model=ItemsPublic)
def read_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> Any:
    """
    Retrieve items.
    """

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Item)
    else:
        count_statement = (
            select(func.count())
            .select_from(Item)
            .where(Item.owner_id == current_user.id)
        )
    if search:
        count_statement = count_statement.where(Item.title.contains(search))
    count = session.exec(count_statement).one()

    statement = select(Item)
    if not current_user.is_superuser:
        statement = statement.where(Item.owner_id == current_user.id)
    if search:
        statement = statement.where(Item.title.contains(search))
    statement = statement.offset(skip).limit(limit)
    items = session.exec(statement).all()

    return ItemsPublic(data=items, count=count)


@router.get("/{id}", response_model=ItemPublic)
def read_item(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get item by ID.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return item


@router.post("/", response_model=ItemPublic)
def create_item(
    *, session: SessionDep, current_user: CurrentUser, item_in: ItemCreate
) -> Any:
    """
    Create new item.
    """
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
    id: uuid.UUID,
    item_in: ItemUpdate,
) -> Any:
    """
    Update an item.
    """
    item = session.get(Item, id)
    if not item:
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
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an item.
    """
    item = session.get(Item, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if not current_user.is_superuser and (item.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(item)
    session.commit()
    return Message(message="Item deleted successfully")


@router.get(
    "/export",
    response_class=PlainTextResponse,
)
def export_items(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
) -> PlainTextResponse:
    """
    Export items as CSV.
    """
    statement = select(Item)
    if not current_user.is_superuser:
        statement = statement.where(Item.owner_id == current_user.id)
    if search:
        statement = statement.where(Item.title.contains(search))
    statement = statement.offset(skip).limit(limit)
    items = session.exec(statement).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "name", "created_at"])
    for item in items:
        writer.writerow([str(item.id), getattr(item, "title", ""), ""])

    csv_content = output.getvalue()
    headers = {
        "Content-Disposition": 'attachment; filename="items.csv"',
        "Content-Type": "text/csv; charset=utf-8",
    }
    return PlainTextResponse(content=csv_content, headers=headers)
