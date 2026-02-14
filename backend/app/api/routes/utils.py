from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message
from app.notifications import get_notification_service

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr, background_tasks: BackgroundTasks) -> Message:
    """
    Test emails.
    """
    notifications = get_notification_service()
    background_tasks.add_task(notifications.send_test_email, email_to=email_to)
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
