from app.services.celery_worker import celery
import os
from datetime import datetime, timedelta

@celery.task
def send_otp_email_task(email: str, otp: str):
    try:
        from app.services.email_service import send_otp_email
        send_otp_email(email, otp)
        print(f"OTP email sent to {email} ✅")
    except Exception as e:
        print(f"Failed to send OTP email: {str(e)}")


@celery.task
def send_welcome_email_task(email: str):
    try:
        import resend
        resend.api_key = os.getenv("RESEND_API_KEY")
        resend.Emails.send({
            "from": "Expense Tracker <onboarding@resend.dev>",
            "to": email,
            "subject": "Welcome to Expense Tracker! 🎉",
            "html": """
            <div style="font-family:sans-serif;max-width:400px;margin:auto;padding:32px;border:1px solid #dde8d8;border-radius:12px">
                <h2 style="color:#2d6a4f">Welcome to Expense Tracker AI! 🌿</h2>
                <p>Your email has been verified successfully.</p>
                <p>You can now log in and start tracking your expenses with AI.</p>
                <a href="https://shekjoyeb63-ai.github.io/Expense-Tracker-with-AI/"
                   style="display:inline-block;margin-top:16px;padding:12px 24px;background:#2d6a4f;color:white;border-radius:8px;text-decoration:none;font-weight:600">
                   Go to App →
                </a>
                <p style="color:#6b8f71;font-size:13px;margin-top:24px">Happy tracking! 🎉</p>
            </div>
            """
        })
        print(f"Welcome email sent to {email} ✅")
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")


@celery.task
def send_monthly_summary_task(user_id: int):
    try:
        import resend
        from app.models.tables import sesssionLocal, Expenses, User

        resend.api_key = os.getenv("RESEND_API_KEY")
        db = sesssionLocal()

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
            print(f"No expenses for user {user_id} last month, skipping.")
            return

        category_totals = {}
        total = 0
        for exp in expenses:
            category_totals[exp.category] = category_totals.get(exp.category, 0) + exp.amount
            total += exp.amount

        # Build HTML rows for each category
        rows = "".join([
            f"""<tr>
                <td style="padding:10px;border-bottom:1px solid #dde8d8">{cat}</td>
                <td style="padding:10px;border-bottom:1px solid #dde8d8;text-align:right;color:#2d6a4f;font-weight:600">₹{amt:,.2f}</td>
            </tr>"""
            for cat, amt in sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        ])

        resend.Emails.send({
            "from": "Expense Tracker <onboarding@resend.dev>",
            "to": user.email,
            "subject": f"Monthly Summary — {first_day.strftime('%B %Y')} 📊",
            "html": f"""
            <div style="font-family:sans-serif;max-width:500px;margin:auto;padding:32px;border:1px solid #dde8d8;border-radius:12px">
                <h2 style="color:#2d6a4f">Monthly Summary 📊</h2>
                <p style="color:#6b8f71">{first_day.strftime('%B %Y')}</p>

                <table style="width:100%;border-collapse:collapse;margin:24px 0">
                    <thead>
                        <tr style="background:#d8f3dc">
                            <th style="padding:10px;text-align:left;color:#2d6a4f">Category</th>
                            <th style="padding:10px;text-align:right;color:#2d6a4f">Amount</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>

                <div style="background:#d8f3dc;border-radius:8px;padding:16px;display:flex;justify-content:space-between">
                    <span style="font-weight:600;color:#2d6a4f">Total Spent</span>
                    <span style="font-weight:700;font-size:20px;color:#2d6a4f">₹{total:,.2f}</span>
                </div>

                <p style="color:#6b8f71;font-size:13px;margin-top:24px">
                    Keep tracking your expenses to stay on top of your finances! 🌿
                </p>
                <a href="https://shekjoyeb63-ai.github.io/Expense-Tracker-with-AI/"
                   style="display:inline-block;margin-top:8px;padding:10px 20px;background:#2d6a4f;color:white;border-radius:8px;text-decoration:none;font-weight:600">
                   View Dashboard →
                </a>
            </div>
            """
        })
        print(f"Monthly summary sent to {user.email} ✅")

    except Exception as e:
        print(f"Monthly summary failed: {str(e)}")
    finally:
        db.close()