from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import Membership, Organization, User, UserCreate

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

    # Seed two example organizations and memberships
    org1 = session.exec(
        select(Organization).where(Organization.name == "Example Org 1")
    ).first()
    if not org1:
        org1 = Organization(name="Example Org 1", owner_id=user.id)
        session.add(org1)
        session.commit()
        session.refresh(org1)

    org2 = session.exec(
        select(Organization).where(Organization.name == "Example Org 2")
    ).first()
    if not org2:
        org2 = Organization(name="Example Org 2", owner_id=user.id)
        session.add(org2)
        session.commit()
        session.refresh(org2)

    # Ensure superuser is admin in both orgs
    for org in (org1, org2):
        membership = session.get(Membership, (user.id, org.id))
        if not membership:
            membership = Membership(user_id=user.id, org_id=org.id, role="admin")
            session.add(membership)
            session.commit()
