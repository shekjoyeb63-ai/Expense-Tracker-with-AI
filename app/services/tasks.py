from app.services.celery_worker import celery
from app.services.email_service import send_otp_email
import os
from datetime import datetime, timedelta

@celery.task
def send_otp_email_task(email: str, otp: str):
    try:
        send_otp_email(email, otp)
        print(f"OTP email sent to {email} ✅")
    except Exception as e:
        print(f"Failed to send OTP email: {str(e)}")

@celery.task
def send_welcome_email_task(email: str):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    try:
        sender = os.getenv("MAIL_EMAIL")
        password = os.getenv("MAIL_PASSWORD")
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = email
        msg["Subject"] = "Welcome to Expense Tracker! 🎉"
        body = """
        Welcome to Expense Tracker!
        Your account has been verified. You can now login.
        Happy tracking!
        """
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, email, msg.as_string())
        print(f"Welcome email sent to {email} ✅")
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")

@celery.task
def send_monthly_summary_task(user_id: int):
    # ← ALL imports inside the function
    import smtplib
    import os
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from app.models.tables import sesssionLocal, Expenses, User  # ← moved here

    db = sesssionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        today = datetime.now()
        first_day = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day = today.replace(day=1) - timedelta(days=1)
        expenses = db.query(Expenses).filter(
            Expenses.user_id == user_id,
            Expenses.date >= first_day.strftime("%Y-%m-%d"),
            Expenses.date <= last_day.strftime("%Y-%m-%d")
        ).all()
        if not expenses:
            return
        category_totals = {}
        total = 0
        for exp in expenses:
            category_totals[exp.category] = category_totals.get(exp.category, 0) + exp.amount
            total += exp.amount
        summary = "\n".join([f"  {cat}: ₹{amt:.2f}" for cat, amt in category_totals.items()])
        sender = os.getenv("MAIL_EMAIL")
        password = os.getenv("MAIL_PASSWORD")
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = user.email
        msg["Subject"] = f"Monthly Summary — {first_day.strftime('%B %Y')}"
        body = f"""Hi!\n\nSummary for {first_day.strftime('%B %Y')}:\n{summary}\n\nTotal: ₹{total:.2f}"""
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, user.email, msg.as_string())
        print(f"Monthly summary sent to {user.email} ✅")
    except Exception as e:
        print(f"Monthly summary failed: {str(e)}")
    finally:
        db.close()