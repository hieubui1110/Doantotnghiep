import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.models.operator import Operator


def send_verification_email(operator: Operator, token: str) -> None:
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    subject = "Xac thuc email tai khoan Traffic Monitoring System"
    body = (
        f"Xin chao {operator.full_name or operator.username},\n\n"
        "Vui long xac thuc email bang lien ket sau:\n"
        f"{verification_url}\n\n"
        "Lien ket se het han theo cau hinh cua he thong.\n"
    )

    if not settings.SMTP_HOST:
        print("[email-verification] SMTP_HOST is not configured.")
        print(f"[email-verification] Send this verification link to {operator.email}: {verification_url}")
        return

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = operator.email
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
