from app.notifications import provider
from app.utils import (
    EmailData,
    generate_new_account_email,
    generate_reset_password_email,
    generate_test_email,
)


def send_test_email(*, email_to: str) -> EmailData:
    email = generate_test_email(email_to=email_to)
    provider.send(email_to=email_to, subject=email.subject, html_content=email.html_content)
    return email


def send_welcome_email(*, email_to: str, username: str, password: str) -> EmailData:
    email = generate_new_account_email(email_to=email_to, username=username, password=password)
    provider.send(email_to=email_to, subject=email.subject, html_content=email.html_content)
    return email


def send_password_recovery_email(*, email_to: str, email: str, token: str) -> EmailData:
    email_data = generate_reset_password_email(email_to=email_to, email=email, token=token)
    provider.send(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return email_data