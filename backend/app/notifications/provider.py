from abc import ABC, abstractmethod


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, *, email_to: str, subject: str, html_content: str) -> None:  # pragma: no cover - interface
        ...