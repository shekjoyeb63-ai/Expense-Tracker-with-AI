import smtplib
import random
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.services.redis_client import redis_client

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def store_otp(email: str, otp: str):
    redis_client.setex(f"otp:{email}", 300, otp)

def verify_otp(email: str, otp: str) -> bool:
    stored_otp = redis_client.get(f"otp:{email}")

    if not stored_otp:
        return False  

    if stored_otp == otp:
        redis_client.delete(f"otp:{email}")
        return True

    return False  

def send_otp_email(email: str, otp: str):
    sender = os.getenv("MAIL_EMAIL")
    password = os.getenv("MAIL_PASSWORD")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = email
    msg["Subject"] = "Your Expense Tracker OTP"

    body = f"""
    Hello!

    Your OTP for Expense Tracker verification is:

    {otp}

    This OTP expires in 5 minutes.
    Do not share it with anyone.

    """
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()  # encrypt the connection
        server.login(sender, password)
        server.sendmail(sender, email, msg.as_string())