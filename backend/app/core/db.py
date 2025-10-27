from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import (
    ItemCreate,
    Membership,
    Organization,
    RoleEnum,
    User,
    UserCreate,
)

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

    superuser = session.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    ).first()
    if not superuser:
        user_in = UserCreate(
            email=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            is_superuser=True,
        )
        superuser = crud.create_user(session=session, user_create=user_in)

    # ensure test user exists
    test_user = session.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    if not test_user:
        test_user = crud.create_user(
            session=session,
            user_create=UserCreate(email=settings.EMAIL_TEST_USER, password="testpassword123"),
        )

    # Seed two organizations and memberships
    org1 = session.exec(select(Organization).where(Organization.name == "Acme")).first()
    if not org1:
        org1 = Organization(name="Acme")
        session.add(org1)
        session.commit()
        session.refresh(org1)
    org2 = session.exec(select(Organization).where(Organization.name == "Globex")).first()
    if not org2:
        org2 = Organization(name="Globex")
        session.add(org2)
        session.commit()
        session.refresh(org2)

    # add memberships (idempotent)
    def ensure_membership(user_id, org_id, role: RoleEnum):
        exists = session.exec(
            select(Membership).where(Membership.user_id == user_id, Membership.org_id == org_id)
        ).first()
        if not exists:
            m = Membership(user_id=user_id, org_id=org_id, role=role)
            session.add(m)
            session.commit()

    if superuser:
        ensure_membership(superuser.id, org1.id, RoleEnum.admin)
        ensure_membership(superuser.id, org2.id, RoleEnum.admin)
    if test_user:
        ensure_membership(test_user.id, org1.id, RoleEnum.member)

    # create a sample item in org1 for superuser
    if superuser:
        existing_item = session.exec(
            select(User, Organization)
            .where(User.id == superuser.id)
        ).first()
        item_in = ItemCreate(title="Welcome Item", description="Seeded item")
        # create via crud to preserve pattern; org set at route usually, set manually here
        from app.models import Item
        item = session.exec(select(Item).where(Item.title == item_in.title)).first()
        if not item:
            item = Item.model_validate(item_in, update={"owner_id": superuser.id, "org_id": org1.id})
            session.add(item)
            session.commit()
