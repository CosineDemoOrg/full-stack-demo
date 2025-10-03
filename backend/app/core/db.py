from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Organization, Membership, RoleEnum, Item, ItemCreate

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Tables should be created with Alembic migrations
    # But if you don't want to use migrations, create
    # the tables un-commenting the next lines
    # from sqlmodel import SQLModel

    # This works because the models are already imported and registered from app.models
    # SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        user = crud.create_user(session=session, user_create=user_in)

    # Seed two organizations and users/memberships
    existing_orgs = session.exec(select(Organization)).all()
    if not existing_orgs:
        org1 = Organization(name="Acme Inc.")
        org2 = Organization(name="Globex LLC")
        session.add(org1)
        session.add(org2)
        session.commit()
        session.refresh(org1)
        session.refresh(org2)

        # Create two regular users
        u1 = crud.get_user_by_email(session=session, email="user1@example.com")
        if not u1:
            u1 = crud.create_user(
                session=session,
                user_create=UserCreate(email="user1@example.com", password="password123", full_name="User One"),
            )
        u2 = crud.get_user_by_email(session=session, email="user2@example.com")
        if not u2:
            u2 = crud.create_user(
                session=session,
                user_create=UserCreate(email="user2@example.com", password="password123", full_name="User Two"),
            )

        # Superuser is admin in both orgs
        session.add(Membership(user_id=user.id, org_id=org1.id, role=RoleEnum.admin, is_active=True))
        session.add(Membership(user_id=user.id, org_id=org2.id, role=RoleEnum.admin, is_active=True))
        # u1 admin in org1, member in org2 (pending)
        session.add(Membership(user_id=u1.id, org_id=org1.id, role=RoleEnum.admin, is_active=True))
        session.add(Membership(user_id=u1.id, org_id=org2.id, role=RoleEnum.member, is_active=False))
        # u2 member in org1, admin in org2
        session.add(Membership(user_id=u2.id, org_id=org1.id, role=RoleEnum.member, is_active=True))
        session.add(Membership(user_id=u2.id, org_id=org2.id, role=RoleEnum.admin, is_active=True))
        session.commit()

        # Seed some items per org
        session.add(Item.model_validate(ItemCreate(title="Org1 Item A", description="First"), update={"owner_id": u1.id, "org_id": org1.id}))
        session.add(Item.model_validate(ItemCreate(title="Org1 Item B"), update={"owner_id": u2.id, "org_id": org1.id}))
        session.add(Item.model_validate(ItemCreate(title="Org2 Item X"), update={"owner_id": u2.id, "org_id": org2.id}))
        session.commit()
