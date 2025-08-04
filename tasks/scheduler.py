from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
from models.users import User
from pytz import timezone
from utilities.insight_generator import generate_and_save_insight
from models.insights import InsightPeriod

def generate_insights(period: InsightPeriod):
    db: Session = SessionLocal()
    try:
        today = date.today()
        if period == InsightPeriod.DAILY:
            start_date = today - timedelta(days=1)  # Previous day
        elif period == InsightPeriod.WEEKLY:
            # Previous week: Monday to Sunday
            last_monday = today - timedelta(days=today.weekday() + 7)
            start_date = last_monday
        elif period == InsightPeriod.MONTHLY:
            # Previous month: 1st to last day
            first_of_this_month = today.replace(day=1)
            last_month_end = first_of_this_month - timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            start_date= last_month_start
        else:
            print(f"❌ Unknown period: {period}")
            db.close()
            return
        users = db.query(User).all()
        for user in users:
            generate_and_save_insight(db, user_id=user.id, period=period, start_date=start_date)
        print(f"✅ {period.value.title()} insights generated for {len(users)} users for {start_date}.")
    except Exception as e:
        print(f"❌ Error generating {period.value.title()} insights: {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Daily: every day at midnight
    scheduler.add_job(
        lambda: generate_insights(InsightPeriod.DAILY),
        "cron",
        hour=0,
        minute=0,
        timezone=timezone("Asia/Karachi"),
    )
    # Weekly: every Monday at 1:00 AM (for previous week)
    scheduler.add_job(
        lambda: generate_insights(InsightPeriod.WEEKLY),
        "cron",
        day_of_week="mon",
        hour=1,
        minute=0,
        timezone=timezone("Asia/Karachi"),
    )
    # Monthly: 1st of each month at 2:00 AM (for previous month)
    scheduler.add_job(
        lambda: generate_insights(InsightPeriod.MONTHLY),
        "cron",
        day=1,
        hour=2,
        minute=0,
        timezone=timezone("Asia/Karachi"),
    )
    scheduler.start()
    print("🕓 Scheduler started for generating daily, weekly, and monthly insights.")



# # tasks/scheduler.py

# from apscheduler.schedulers.background import BackgroundScheduler
# from datetime import date
# from sqlalchemy.orm import Session
# from database import SessionLocal
# from users.models import User
# from pytz import timezone
# from utilities.insight_generator import generate_daily_insight

# import os
# from dotenv import load_dotenv

# load_dotenv()

# def generate_insights():
#     for all users Call
#     generate_daily_insight(db: Session, user_id: int, target_date: date)

# def start_scheduler():
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(
#         generate_insights,
#         "cron",
#         hour=0,
#         minute=0,
#         timezone=timezone("Asia/Karachi"),
#     )  # Every day at midnight
#     scheduler.start()
#     print("🕓 Scheduler started for generating insights.")
