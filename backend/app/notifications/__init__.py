from .provider import NotificationProvider
from .providers.console import ConsoleProvider
from .providers.smtp import SmtpProvider
from app.core.config import settings


def get_provider() -> NotificationProvider:
    if settings.NOTIFICATIONS_PROVIDER == "smtp":
        return SmtpProvider()
    return ConsoleProvider()


provider = get_provider()