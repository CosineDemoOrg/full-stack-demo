from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message
from app.notifications.service import notifications_service

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
    background_tasks.add_task(
        notifications_service.send_test_email,
        email_to=email_to,
    )
    return Message(message="Test email scheduled")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
