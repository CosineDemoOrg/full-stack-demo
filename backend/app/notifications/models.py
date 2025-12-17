from dataclasses import dataclass


@dataclass
class EmailData:
    email_to: str
    subject: str
    html_content: str