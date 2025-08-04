import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class SugarType(enum.Enum):
    FASTING = "FASTING"
    RANDOM = "RANDOM"
    # AFTER_MEAL = "after_meal"
    # BEDTIME = "bedtime"
    # POST_PRANDIAL_2H = "post_prandial_2h"

class SugarLog(Base):
    __tablename__ = "sugar_logs"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("sugar_schedules.id"), nullable=True, index=True)

    value = Column(Float, nullable=False)
    type = Column(Enum(SugarType), nullable=False)
    notes = Column(String(500), nullable=True)

    checked_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    schedule = relationship("SugarSchedule", back_populates="sugar_logs")

    __table_args__ = (
        CheckConstraint("value > 0 AND value < 1000", name="check_sugar_value_range"),
    )