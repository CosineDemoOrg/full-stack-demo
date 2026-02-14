from unittest.mock import MagicMock, patch

import pytest

from app.notifications.console import ConsoleProvider
from app.notifications.smtp import SMTPProvider
from app.core.config import settings


def test_console_provider_runs():
    provider = ConsoleProvider()
    provider.send_html(email_to="user@example.com", subject="Hello", html_content="<p>Hi</p>")


def test_smtp_provider_raises_if_not_configured(monkeypatch):
    # ensure disabled
    monkeypatch.setattr(settings, "SMTP_HOST", None)
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", None)
    provider = SMTPProvider()
    with pytest.raises(RuntimeError):
        provider.send_html(email_to="user@example.com", subject="Hello", html_content="<p>Hi</p>")


@patch("app.notifications.smtp.emails.Message")
def test_smtp_provider_sends(Message: MagicMock, monkeypatch):
    # minimal configuration
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_TLS", True)
    monkeypatch.setattr(settings, "SMTP_SSL", False)
    monkeypatch.setattr(settings, "SMTP_USER", "smtpuser")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtppass")
    monkeypatch.setattr(settings, "EMAILS_FROM_NAME", "Project")
    monkeypatch.setattr(settings, "EMAILS_FROM_EMAIL", "info@example.com")

    provider = SMTPProvider()
    provider.send_html(email_to="user@example.com", subject="Hello", html_content="<p>Hi</p>")
    # verify message and send were called with expected args
    Message.assert_called_once()
    Message.return_value.send.assert_called_once()