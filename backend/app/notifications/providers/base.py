from dataclasses import dataclass
from typing import Protocol


@dataclass
class EmailMessage:
    to: str
    subject: str
    html: str


class NotificationProvider(Protocol):
    def send(self, message: EmailMessage) -> None:  # pragma: no cover - protocol
        ...