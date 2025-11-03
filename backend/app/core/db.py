from sqlmodel import Session, create_engine, select

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, OrganizationCreate, MembershipCreate, Role, ItemCreate

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

    # Seed two orgs + users if not present
    # Create users
    user1 = crud.get_user_by_email(session=session, email="alice@example.com")
    if not user1:
        user1 = crud.create_user(session=session, user_create=UserCreate(email="alice@example.com", password="alicepass"))
    user2 = crud.get_user_by_email(session=session, email="bob@example.com")
    if not user2:
        user2 = crud.create_user(session=session, user_create=UserCreate(email="bob@example.com", password="bobpass"))

    # Create orgs
    from app.models import Organization
    orgA = session.exec(select(Organization).where(Organization.name == "Org A")).first()
    if not orgA:
        orgA = crud.create_org(session=session, org_in=OrganizationCreate(name="Org A", description="Seed Org A"))
        # memberships
        session.add_all([
            # superuser as admin of all orgs for convenience
            ])
        session.commit()
    orgB = session.exec(select(Organization).where(Organization.name == "Org B")).first()
    if not orgB:
        orgB = crud.create_org(session=session, org_in=OrganizationCreate(name="Org B", description="Seed Org B"))

    # Ensure memberships
    def ensure_membership(u: User, o: Organization, role: Role):
        from app.models import Membership
        existing = session.exec(select(Membership).where(Membership.user_id == u.id, Membership.org_id == o.id)).first()
        if not existing:
            session.add(MembershipCreate)  # type: ignore

    # Create actual memberships
    session.add_all([
        # alice admin of Org A
        ])
    session.commit()
    # Using CRUD helpers
    crud.add_membership(session=session, membership_in=MembershipCreate(user_id=user1.id, org_id=orgA.id, role=Role.admin))
    crud.add_membership(session=session, membership_in=MembershipCreate(user_id=user2.id, org_id=orgA.id, role=Role.member))
    crud.add_membership(session=session, membership_in=MembershipCreate(user_id=user2.id, org_id=orgB.id, role=Role.admin))

    # Seed some items under orgs
    crud.create_item(session=session, item_in=ItemCreate(title="Org A Item 1"), owner_id=user1.id, org_id=orgA.id)
    crud.create_item(session=session, item_in=ItemCreate(title="Org A Item 2"), owner_id=user2.id, org_id=orgA.id)
    crud.create_item(session=session, item_in=ItemCreate(title="Org B Item 1"), owner_id=user2.id, org_id=orgB.id)
