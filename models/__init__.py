# Backend/models/__init__.py

# This file imports all models, making them available
# to SQLAlchemy and other parts of the application from a single point.
# This solves circular import and load-order issues.

from .users import User
from .chats import Chat
from .messages import Message
from .medicines import Medicine
from .medications import Medication
from .medication_schedules import MedicationSchedule
from .medication_logs import MedicationLog
from .bp_schedules import BloodPressureSchedule
from .bp_logs import BloodPressureLog
from .sugar_schedules import SugarSchedule
from .sugar_logs import SugarLog, SugarType
from .insights import Insight, InsightPeriod

# You can also define a __all__ variable to control what `from models import *` does, which is good practice.
__all__ = [
    "User",
    "Chat",
    "Message",
    "Medicine",
    "Medication",
    "MedicationSchedule",
    "MedicationLog",
    "BloodPressureSchedule",
    "BloodPressureLog",
    "SugarSchedule",
    "SugarLog",
    "SugarType",
    "Insight",
    "InsightPeriod",
]