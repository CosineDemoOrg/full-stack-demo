from fastapi import BackgroundTasks

from app.notifications import get_notification_provider
from app.utils import generate_new_account_email, generate_reset_password_email

_provider = get_notification_provider()


def send_welcome_email(
    *,
    email_to: str,
    username: str,
    password: str,
    background_tasks: BackgroundTasks | None = None,
) -> None:
    email_data = generate_new_account_email(
        email_to=email_to,
        username=username,
        password=password,
    )

    if background_tasks is not None:
        background_tasks.add_task(
            _provider.send_email,
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    else:  # pragma: no cover - used only when called without BackgroundTasks
        _provider.send_email(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )


def send_password_recovery_email(
    *,
    email_to: str,
    email: str,
    token: str,
    background_tasks: BackgroundTasks | None = None,
) -> None:
    email_data = generate_reset_password_email(
        email_to=email_to,
        email=email,
        token=token,
    )

    if background_tasks is not None:
        background_tasks.add_task(
            _provider.send_email,
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    else:  # pragma: no cover - used only when called without BackgroundTasks
        _provider.send_email(
            email_to=email_to,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )