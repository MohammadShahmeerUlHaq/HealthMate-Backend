import os
from email.message import EmailMessage
import smtplib
from dotenv import load_dotenv

load_dotenv()

sender_email = os.getenv("SENDER_EMAIL")
sender_password = os.getenv("SENDER_PASSWORD")


def send_email(recipient_email: str, subject: str, body: str):
    if not sender_email or not sender_password:
        raise RuntimeError("Email credentials not set in environment variables.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
            print("Email sent")
    except Exception as e:
        print(f"Email failed: {e}")
