from langchain.tools import tool
from sqlalchemy.orm import Session
from typing import Optional
from crud.bp_logs import get_logs_by_user_id, get_logs_by_date, get_logs_by_date_range, create_bp_log
from crud.sugar_logs import get_sugar_logs_by_user, get_sugar_logs_by_date, get_sugar_logs_by_date_range, create_sugar_log
from crud.medications import get_user_medicines, count_medications, create_medication_with_schedules, get_user_medications
from crud.bp_schedules import get_user_bp_schedules, create_bp_schedule
from crud.sugar_schedules import get_user_sugar_schedules, create_sugar_schedule
from crud.medication_logs import get_logs_by_medicine, get_logs_by_user, get_logs_by_date as get_med_logs_by_date, get_logs_by_date_range as get_med_logs_by_date_range, create_log as create_med_log
from crud.medicines import get_medicines
from crud.users import get_user, update_user
from crud.insights import get_insight_by_period_and_date
import contextvars

# Context variable for db session
_db_ctx: contextvars.ContextVar[Optional[Session]] = contextvars.ContextVar("db", default=None)
_user_ctx: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar("user_id", default=None)

def set_tool_context(db: Session, user_id: int):
    _db_ctx.set(db)
    _user_ctx.set(user_id)

def get_db():
    db = _db_ctx.get()
    if db is None:
        raise RuntimeError("DB session not set in tool context!")
    return db

def get_user_id():
    user_id = _user_ctx.get()
    if user_id is None:
        raise RuntimeError("user_id not set in tool context!")
    return user_id

def serialize_model(obj):
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    # Fallback: serialize common fields
    d = {}
    for attr in dir(obj):
        if not attr.startswith('_') and not callable(getattr(obj, attr)):
            try:
                value = getattr(obj, attr)
                # Avoid recursive relationships
                if isinstance(value, (str, int, float, bool, type(None))):
                    d[attr] = value
            except Exception:
                pass
    return d

def serialize_list(objs):
    return [serialize_model(o) for o in objs]

@tool("get_user_medicines", return_direct=True)
def tool_get_user_medicines():
    """Get a list of medicines prescribed to the current user."""
    db = get_db()
    user_id = get_user_id()
    medicines = get_user_medicines(db, user_id)
    return serialize_list(medicines)

@tool("count_medications", return_direct=True)
def tool_count_medications():
    """Count the number of active medications for the current user."""
    db = get_db()
    user_id = get_user_id()
    return count_medications(db, user_id)

@tool("create_medication_with_schedules", return_direct=True)
def tool_create_medication_with_schedules(payload):
    """Create a new medication and its schedules for the current user."""
    db = get_db()
    user_id = get_user_id()
    result = create_medication_with_schedules(db, user_id, payload)
    return serialize_model(result) if result else result

@tool("get_user_medications", return_direct=True)
def tool_get_user_medications():
    """Get all medications for the current user."""
    db = get_db()
    user_id = get_user_id()
    meds = get_user_medications(db, user_id)
    return serialize_list(meds)

@tool("get_logs_by_medicine", return_direct=True)
def tool_get_logs_by_medicine(medicine_id: int):
    """Get medication logs for the current user by medicine ID."""
    db = get_db()
    user_id = get_user_id()
    logs = get_logs_by_medicine(db, user_id, medicine_id)
    return serialize_list(logs)

@tool("get_logs_by_user_id", return_direct=True)
def tool_get_logs_by_user_id():
    """Get all blood pressure logs for the current user."""
    db = get_db()
    user_id = get_user_id()
    logs = get_logs_by_user_id(db, user_id)
    return serialize_list(logs)

@tool("get_logs_by_date", return_direct=True)
def tool_get_logs_by_date(target_date):
    """Get blood pressure logs for the current user on a specific date."""
    db = get_db()
    user_id = get_user_id()
    logs = get_logs_by_date(db, user_id, target_date)
    return serialize_list(logs)

@tool("get_logs_by_date_range", return_direct=True)
def tool_get_logs_by_date_range(start_date, end_date):
    """Get blood pressure logs for the current user within a date range."""
    db = get_db()
    user_id = get_user_id()
    logs = get_logs_by_date_range(db, user_id, start_date, end_date)
    return serialize_list(logs)

@tool("create_bp_log", return_direct=True)
def tool_create_bp_log(schedule_id: int, data):
    """Create a new blood pressure log for the current user."""
    db = get_db()
    user_id = get_user_id()
    result = create_bp_log(db, user_id, schedule_id, data)
    return serialize_model(result) if result else result

@tool("get_sugar_logs_by_user", return_direct=True)
def tool_get_sugar_logs_by_user():
    """Get all sugar logs for the current user."""
    db = get_db()
    user_id = get_user_id()
    logs = get_sugar_logs_by_user(db, user_id)
    return serialize_list(logs)

@tool("get_sugar_logs_by_date", return_direct=True)
def tool_get_sugar_logs_by_date(target_date):
    """Get sugar logs for the current user on a specific date."""
    db = get_db()
    user_id = get_user_id()
    logs = get_sugar_logs_by_date(db, user_id, target_date)
    return serialize_list(logs)

@tool("get_sugar_logs_by_date_range", return_direct=True)
def tool_get_sugar_logs_by_date_range(start, end):
    """Get sugar logs for the current user within a date range."""
    db = get_db()
    user_id = get_user_id()
    logs = get_sugar_logs_by_date_range(db, user_id, start, end)
    return serialize_list(logs)

@tool("create_sugar_log", return_direct=True)
def tool_create_sugar_log(schedule_id: int, data):
    """Create a new sugar log for the current user."""
    db = get_db()
    user_id = get_user_id()
    result = create_sugar_log(db, user_id, schedule_id, data)
    return serialize_model(result) if result else result

@tool("get_user_bp_schedules", return_direct=True)
def tool_get_user_bp_schedules():
    """Get all blood pressure schedules for the current user."""
    db = get_db()
    user_id = get_user_id()
    schedules = get_user_bp_schedules(db, user_id)
    return serialize_list(schedules)

@tool("create_bp_schedule", return_direct=True)
def tool_create_bp_schedule(payload):
    """Create a new blood pressure schedule for the current user."""
    db = get_db()
    user_id = get_user_id()
    result = create_bp_schedule(db, user_id, payload)
    return serialize_model(result) if result else result

@tool("get_user_sugar_schedules", return_direct=True)
def tool_get_user_sugar_schedules():
    """Get all sugar schedules for the current user."""
    db = get_db()
    user_id = get_user_id()
    schedules = get_user_sugar_schedules(db, user_id)
    return serialize_list(schedules)

@tool("create_sugar_schedule", return_direct=True)
def tool_create_sugar_schedule(payload):
    """Create a new sugar schedule for the current user."""
    db = get_db()
    user_id = get_user_id()
    result = create_sugar_schedule(db, user_id, payload)
    return serialize_model(result) if result else result

@tool("get_logs_by_user", return_direct=True)
def tool_get_logs_by_user():
    """Get all medication logs for the current user."""
    db = get_db()
    user_id = get_user_id()
    logs = get_logs_by_user(db, user_id)
    return serialize_list(logs)

@tool("get_med_logs_by_date", return_direct=True)
def tool_get_med_logs_by_date(target_date):
    """Get medication logs for the current user on a specific date."""
    db = get_db()
    user_id = get_user_id()
    logs = get_med_logs_by_date(db, user_id, target_date)
    return serialize_list(logs)

@tool("get_med_logs_by_date_range", return_direct=True)
def tool_get_med_logs_by_date_range(start_date, end_date):
    """Get medication logs for the current user within a date range."""
    db = get_db()
    user_id = get_user_id()
    logs = get_med_logs_by_date_range(db, user_id, start_date, end_date)
    return serialize_list(logs)

@tool("create_med_log", return_direct=True)
def tool_create_med_log(schedule_id: int, log_data,):
    """Create a new medication log for the current user."""
    db = get_db()
    user_id = get_user_id()
    result = create_med_log(db, schedule_id, log_data, user_id)
    return serialize_model(result) if result else result

@tool("get_medicines", return_direct=True)
def tool_get_medicines():
    """Get all available medicines in the system."""
    db = get_db()
    medicines = get_medicines(db)
    return serialize_list(medicines)

@tool("get_user", return_direct=True)
def tool_get_user():
    """Get user profile information for the current user."""
    db = get_db()
    user_id = get_user_id()
    user = get_user(db, user_id)
    return serialize_model(user) if user else user

@tool("update_user", return_direct=True)
def tool_update_user(user_data):
    """Update user profile information for the current user."""
    db = get_db()
    user_id = get_user_id()
    result = update_user(db, user_id, user_data)
    return serialize_model(result) if result else result

@tool("get_insight_by_period_and_date", return_direct=True)
def tool_get_insight_by_period_and_date(period, start_date):
    """Get health insight for the current user for a specific period and date."""
    db = get_db()
    user_id = get_user_id()
    result = get_insight_by_period_and_date(db, user_id, period, start_date)
    return serialize_model(result) if result else result

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
] 