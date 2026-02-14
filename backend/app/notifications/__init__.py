from .base import NotificationProvider
from .console import ConsoleProvider
from .smtp import SMTPProvider
from app.core.config import settings


def get_provider() -> NotificationProvider:
    if settings.NOTIFICATIONS_PROVIDER == "smtp":
        return SMTPProvider()
    return ConsoleProvider()