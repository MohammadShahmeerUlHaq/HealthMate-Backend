import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class SugarSchedule(Base):
    __tablename__ = "sugar_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    time = Column(Time, nullable=False)  # e.g., 08:00:00
    duration_days = Column(Integer, nullable=False)
    start_date = Column(Date, default=date.today, nullable=False)
    end_date = Column(Date, nullable=True)  # Calculated: start_date + duration_days
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sugar_schedules")
    sugar_logs = relationship("SugarLog", back_populates="schedule", cascade="all, delete")

    __table_args__ = (
        CheckConstraint("duration_days > 0", name="check_sugar_schedule_positive_duration"),
    )