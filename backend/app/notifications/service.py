from app.utils import (
    EmailData,
    generate_new_account_email,
    generate_reset_password_email,
    generate_test_email,
)

from .providers import EmailMessage, NotificationProvider, get_notification_provider


def _to_email_message(email_to: str, email_data: EmailData) -> EmailMessage:
    return EmailMessage(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )


def send_welcome_email(
    *, email_to: str, username: str, password: str, provider: NotificationProvider | None = None
) -> None:
    """Send a welcome email to a new user."""
    email_data = generate_new_account_email(
        email_to=email_to, username=username, password=password
    )
    message = _to_email_message(email_to=email_to, email_data=email_data)
    (provider or get_notification_provider()).send_email(message)


def send_password_recovery_email(
    *, email_to: str, email: str, token: str, provider: NotificationProvider | None = None
) -> None:
    """Send a password recovery email."""
    email_data = generate_reset_password_email(
        email_to=email_to,
        email=email,
        token=token,
    )
    message = _to_email_message(email_to=email_to, email_data=email_data)
    (provider or get_notification_provider()).send_email(message)


def send_test_email(
    *, email_to: str, provider: NotificationProvider | None = None
) -> None:
    """Send a test email."""
    email_data = generate_test_email(email_to=email_to)
    message = _to_email_message(email_to=email_to, email_data=email_data)
    (provider or get_notification_provider()).send_email(message)