from dataclasses import dataclass
from typing import Protocol


@dataclass
class Notification:
    to: str
    subject: str
    html: str


class NotificationProvider(Protocol):
    def send(self, notification: Notification) -> None:  # pragma: no cover
        ...


class NotificationError(RuntimeError):
    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause