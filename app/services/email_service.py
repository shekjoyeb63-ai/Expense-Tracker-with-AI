import random
import os
import resend
from app.services.redis_client import redis_client

def get_resend():
    resend.api_key = os.getenv("RESEND_API_KEY")
    return resend

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
    r = get_resend()
    r.Emails.send({
        "from": "Expense Tracker <onboarding@resend.dev>",
        "to": email,
        "subject": "Your Expense Tracker OTP",
        "html": f"""
        <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;border:1px solid #dde8d8;border-radius:12px">
            <h2 style="color:#2d6a4f">Expense Tracker AI</h2>
            <p>Your verification code is:</p>
            <div style="font-size:36px;font-weight:bold;color:#2d6a4f;letter-spacing:8px;margin:24px 0">{otp}</div>
            <p style="color:#6b8f71;font-size:13px">This OTP expires in 5 minutes. Do not share it with anyone.</p>
        </div>
        """
    })