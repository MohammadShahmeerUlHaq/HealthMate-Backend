from sqlalchemy import text
from database import engine

tables = [
    # "users",
    # "chats",
    # "messages",
    # "medicines",
    # "medications",
    # "medication_schedules",
    # "medication_logs",
    "insights"
    # "bp_logs",
    # "bp_schedules",
    # "sugar_logs",
    # "sugar_schedules",
]

with engine.begin() as conn:
    for table in tables:
        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))

print("Tables dropped successfully.")
