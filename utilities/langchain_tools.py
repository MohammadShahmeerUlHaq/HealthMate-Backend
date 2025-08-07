from langchain.tools import tool
from sqlalchemy.orm import Session
from crud.bp_logs import get_logs_by_user_id, get_logs_by_date, get_logs_by_date_range, create_bp_log
from crud.sugar_logs import get_sugar_logs_by_user, get_sugar_logs_by_date, get_sugar_logs_by_date_range, create_sugar_log
from crud.medications import get_user_medicines, count_medications, create_medication_with_schedules, get_user_medications
from crud.bp_schedules import get_user_bp_schedules, create_bp_schedule
from crud.sugar_schedules import get_user_sugar_schedules, create_sugar_schedule
from crud.medication_logs import get_logs_by_medicine, get_logs_by_user, get_logs_by_date as get_med_logs_by_date, get_logs_by_date_range as get_med_logs_by_date_range, create_log as create_med_log
from crud.medicines import get_medicines
from crud.users import get_user, update_user
from crud.insights import get_insight_by_period_and_date
# from crud.chats import get_messages_by_chat, get_last_user_message_by_chat
# from crud.messages import create_message_with_ai

# Each tool is wrapped with @tool and has a clear docstring for the agent

@tool("get_user_medicines", return_direct=True)
def tool_get_user_medicines(db: Session, user_id: int):
    """Get a list of medicines prescribed to a user."""
    return get_user_medicines(db, user_id)

@tool("count_medications", return_direct=True)
def tool_count_medications(db: Session, user_id: int):
    """Count the number of active medications for a user."""
    return count_medications(db, user_id)

@tool("create_medication_with_schedules", return_direct=True)
def tool_create_medication_with_schedules(db: Session, user_id: int, payload):
    """Create a new medication and its schedules for a user."""
    return create_medication_with_schedules(db, user_id, payload)

@tool("get_user_medications", return_direct=True)
def tool_get_user_medications(db: Session, user_id: int):
    """Get all medications for a user."""
    return get_user_medications(db, user_id)

@tool("get_logs_by_medicine", return_direct=True)
def tool_get_logs_by_medicine(db: Session, user_id: int, medicine_id: int):
    """Get medication logs for a user by medicine ID."""
    return get_logs_by_medicine(db, user_id, medicine_id)

@tool("get_logs_by_user_id", return_direct=True)
def tool_get_logs_by_user_id(db: Session, user_id: int):
    """Get all blood pressure logs for a user."""
    return get_logs_by_user_id(db, user_id)

@tool("get_logs_by_date", return_direct=True)
def tool_get_logs_by_date(db: Session, user_id: int, target_date):
    """Get blood pressure logs for a user on a specific date."""
    return get_logs_by_date(db, user_id, target_date)

@tool("get_logs_by_date_range", return_direct=True)
def tool_get_logs_by_date_range(db: Session, user_id: int, start_date, end_date):
    """Get blood pressure logs for a user within a date range."""
    return get_logs_by_date_range(db, user_id, start_date, end_date)

@tool("create_bp_log", return_direct=True)
def tool_create_bp_log(db: Session, user_id: int, schedule_id: int, data):
    """Create a new blood pressure log for a user."""
    return create_bp_log(db, user_id, schedule_id, data)

@tool("get_sugar_logs_by_user", return_direct=True)
def tool_get_sugar_logs_by_user(db: Session, user_id: int):
    """Get all sugar logs for a user."""
    return get_sugar_logs_by_user(db, user_id)

@tool("get_sugar_logs_by_date", return_direct=True)
def tool_get_sugar_logs_by_date(db: Session, user_id: int, target_date):
    """Get sugar logs for a user on a specific date."""
    return get_sugar_logs_by_date(db, user_id, target_date)

@tool("get_sugar_logs_by_date_range", return_direct=True)
def tool_get_sugar_logs_by_date_range(db: Session, user_id: int, start, end):
    """Get sugar logs for a user within a date range."""
    return get_sugar_logs_by_date_range(db, user_id, start, end)

@tool("create_sugar_log", return_direct=True)
def tool_create_sugar_log(db: Session, user_id: int, schedule_id: int, data):
    """Create a new sugar log for a user."""
    return create_sugar_log(db, user_id, schedule_id, data)

@tool("get_user_bp_schedules", return_direct=True)
def tool_get_user_bp_schedules(db: Session, user_id: int):
    """Get all blood pressure schedules for a user."""
    return get_user_bp_schedules(db, user_id)

@tool("create_bp_schedule", return_direct=True)
def tool_create_bp_schedule(db: Session, user_id: int, payload):
    """Create a new blood pressure schedule for a user."""
    return create_bp_schedule(db, user_id, payload)

@tool("get_user_sugar_schedules", return_direct=True)
def tool_get_user_sugar_schedules(db: Session, user_id: int):
    """Get all sugar schedules for a user."""
    return get_user_sugar_schedules(db, user_id)

@tool("create_sugar_schedule", return_direct=True)
def tool_create_sugar_schedule(db: Session, user_id: int, payload):
    """Create a new sugar schedule for a user."""
    return create_sugar_schedule(db, user_id, payload)

@tool("get_logs_by_user", return_direct=True)
def tool_get_logs_by_user(db: Session, user_id: int):
    """Get all medication logs for a user."""
    return get_logs_by_user(db, user_id)

@tool("get_med_logs_by_date", return_direct=True)
def tool_get_med_logs_by_date(db: Session, user_id: int, target_date):
    """Get medication logs for a user on a specific date."""
    return get_med_logs_by_date(db, user_id, target_date)

@tool("get_med_logs_by_date_range", return_direct=True)
def tool_get_med_logs_by_date_range(db: Session, user_id: int, start_date, end_date):
    """Get medication logs for a user within a date range."""
    return get_med_logs_by_date_range(db, user_id, start_date, end_date)

@tool("create_med_log", return_direct=True)
def tool_create_med_log(db: Session, schedule_id: int, log_data, user_id: int):
    """Create a new medication log for a user."""
    return create_med_log(db, schedule_id, log_data, user_id)

@tool("get_medicines", return_direct=True)
def tool_get_medicines(db: Session):
    """Get all available medicines in the system."""
    return get_medicines(db)

@tool("get_user", return_direct=True)
def tool_get_user(db: Session, user_id: int):
    """Get user profile information."""
    return get_user(db, user_id)

@tool("update_user", return_direct=True)
def tool_update_user(db: Session, user_id: int, user_data):
    """Update user profile information."""
    return update_user(db, user_id, user_data)

@tool("get_insight_by_period_and_date", return_direct=True)
def tool_get_insight_by_period_and_date(db: Session, user_id: int, period, start_date):
    """Get health insight for a user for a specific period and date."""
    return get_insight_by_period_and_date(db, user_id, period, start_date)

@tool("get_messages_by_chat", return_direct=True)
def tool_get_messages_by_chat(db: Session, chat_id: int):
    """Get all messages for a specific chat."""
    return get_messages_by_chat(db, chat_id)

@tool("get_last_user_message_by_chat", return_direct=True)
def tool_get_last_user_message_by_chat(db: Session, chat_id: int):
    """Get the last user message for a specific chat."""
    return get_last_user_message_by_chat(db, chat_id)

ALL_TOOLS = [
    tool_get_user_medicines,
    tool_count_medications,
    tool_create_medication_with_schedules,
    tool_get_user_medications,
    tool_get_logs_by_medicine,
    tool_get_logs_by_user_id,
    tool_get_logs_by_date,
    tool_get_logs_by_date_range,
    tool_create_bp_log,
    tool_get_sugar_logs_by_user,
    tool_get_sugar_logs_by_date,
    tool_get_sugar_logs_by_date_range,
    tool_create_sugar_log,
    tool_get_user_bp_schedules,
    tool_create_bp_schedule,
    tool_get_user_sugar_schedules,
    tool_create_sugar_schedule,
    tool_get_logs_by_user,
    tool_get_med_logs_by_date,
    tool_get_med_logs_by_date_range,
    tool_create_med_log,
    tool_get_medicines,
    tool_get_user,
    tool_update_user,
    tool_get_insight_by_period_and_date,
    tool_get_messages_by_chat,
    tool_get_last_user_message_by_chat,
] 