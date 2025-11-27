from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic.networks import EmailStr

from app.api.deps import NotificationProviderDep, get_current_active_superuser
from app.models import Message
from app.notifications import send_test_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(
    email_to: EmailStr,
    background_tasks: BackgroundTasks,
    notification_provider: NotificationProviderDep,
) -> Message:
    """
    Test emails.
    """
    background_tasks.add_task(
        send_test_email,
        email_to=email_to,
        provider=notification_provider,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
