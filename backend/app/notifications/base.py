from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import logging

logger = logging.getLogger(__name__)


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, *, email_to: str, subject: str, html_content: str) -> Any:  # pragma: no cover
        raise NotImplementedError


def log_send_result(provider: str, *, email_to: str, subject: str, result: Any) -> None:
    # Simple structured logging with key=value pairs
    logger.info(
        "notification_send provider=%s email_to=%s subject=%s result=%s",
        provider,
        email_to,
        subject,
        result,
    )