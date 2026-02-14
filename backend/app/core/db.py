from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, Organization, Membership

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

    # Ensure a default organization and membership for the first superuser
    org = session.exec(select(Organization).where(Organization.name == "Default Org")).first()
    if not org:
        org = Organization(name="Default Org", description="Default organization")
        session.add(org)
        session.commit()
        session.refresh(org)
    memb = session.exec(
        select(Membership).where((Membership.user_id == user.id) & (Membership.org_id == org.id))
    ).first()
    if not memb:
        memb = Membership(user_id=user.id, org_id=org.id, role="admin")  # type: ignore
        session.add(memb)
        session.commit()
