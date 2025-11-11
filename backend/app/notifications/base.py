import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    @abstractmethod
    def send_html(self, *, email_to: str, subject: str, html_content: str) -> None:  # pragma: no cover
        """Send an HTML email/notification."""
        raise NotImplementedError