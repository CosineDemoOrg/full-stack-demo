from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class EmailMessage:
    email_to: str
    subject: str
    html_content: str


class NotificationError(Exception):
    """Raised when a notification provider fails to send a message."""


class NotificationProvider(ABC):
    @abstractmethod
    def send_email(self, message: EmailMessage) -> None:
        """Send an email notification."""
        raise NotImplementedError