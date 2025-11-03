from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, *, email_to: str, subject: str, html_content: str) -> None:
        """Send a notification (email)."""
        raise NotImplementedError


def get_provider(settings: Any) -> NotificationProvider:
    """Return provider instance based on settings."""
    provider = (settings.NOTIFICATIONS_PROVIDER or "console").lower()
    if provider == "smtp":
        from .smtp import SMTPProvider

        return SMTPProvider(settings=settings)
    # default to console
    from .console import ConsoleProvider

    return ConsoleProvider(settings=settings)