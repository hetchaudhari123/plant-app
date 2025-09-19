import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.config import settings


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = True,
    port: int = 587
):
    """
    Send an email using Gmail SMTP.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject
        body (str): Email body (HTML or plain text)
        is_html (bool): Whether body is HTML or plain text
        port (int): SMTP port (default 587 for TLS)
    """

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = settings.MAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    mime_type = "html" if is_html else "plain"
    msg.attach(MIMEText(body, mime_type))

    try:
        with smtplib.SMTP("smtp.gmail.com", port) as server:
            server.starttls()
            server.login(settings.MAIL_USER, settings.MAIL_PASS)
            server.sendmail(settings.MAIL_USER, to_email, msg.as_string())
            print(f"✅ Email sent to {to_email} with subject '{subject}'")
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        raise
