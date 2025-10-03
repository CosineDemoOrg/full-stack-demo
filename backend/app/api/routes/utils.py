from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic.networks import EmailStr

from app.api.deps import get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email
from app.notifications.service import send_test_email

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
    # Enqueue sending; return immediately for optimistic UX
    background_tasks.add_task(send_test_email, email_to=email_to)
    return Message(message="Test email enqueued")


@router.get("/health-check/")
async def health_check() -> bool:
    return True
