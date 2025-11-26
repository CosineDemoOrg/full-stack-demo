from dataclasses import dataclass


@dataclass
class EmailMessage:
    email_to: str
    subject: str
    html_content: str