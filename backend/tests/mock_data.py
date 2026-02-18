from __future__ import annotations

from uuid import UUID, uuid4

from app.models import (
    ItemCreate,
    ItemUpdate,
    UserCreate,
    UserPublic,
    UserUpdate,
)


# Concrete, reusable users for tests

TEST_USER_ID_1 = uuid4()
TEST_USER_ID_2 = uuid4()

MOCK_USER_CREATE_1 = UserCreate(
    email="alice@example.com",
    username="alice",
    password="strongpassword1",
    full_name="Alice Example",
)

MOCK_USER_CREATE_2 = UserCreate(
    email="bob@example.com",
    username="bob",
    password="strongpassword2",
    full_name="Bob Example",
)

MOCK_USER_UPDATE_1 = UserUpdate(
    full_name="Alice Example Jr.",
)

MOCK_USER_PUBLIC_1 = UserPublic(
    id=TEST_USER_ID_1,
    email="alice@example.com",
    username="alice",
    is_active=True,
    is_superuser=False,
    full_name="Alice Example",
)

MOCK_USER_PUBLIC_2 = UserPublic(
    id=TEST_USER_ID_2,
    email="bob@example.com",
    username="bob",
    is_active=True,
    is_superuser=False,
    full_name="Bob Example",
)


# Concrete, reusable items for tests

TEST_ITEM_ID_1 = uuid4()
TEST_ITEM_ID_2 = uuid4()

MOCK_ITEM_CREATE_1 = ItemCreate(
    title="Example item 1",
    description="The first example item used in tests.",
)

MOCK_ITEM_CREATE_2 = ItemCreate(
    title="Example item 2",
    description="The second example item used in tests.",
)

MOCK_ITEM_UPDATE_1 = ItemUpdate(
    title="Updated example item 1",
    description="Updated description for example item 1.",
)