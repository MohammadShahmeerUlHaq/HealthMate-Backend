import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class BloodPressureLog(Base):
    __tablename__ = "bp_logs"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("bp_schedules.id"), nullable=False, index=True)

    systolic = Column(Integer, nullable=False)
    diastolic = Column(Integer, nullable=False)
    pulse = Column(Integer, nullable=True)
    notes = Column(String(500), nullable=True)

    checked_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    schedule = relationship("BloodPressureSchedule", back_populates="logs")

    __table_args__ = (
        CheckConstraint("systolic > 0 AND systolic < 300", name="check_systolic_range"),
        CheckConstraint("diastolic > 0 AND diastolic < 200", name="check_diastolic_range"),
        CheckConstraint("pulse IS NULL OR (pulse > 0 AND pulse < 250)", name="check_pulse_range"),
        CheckConstraint("systolic > diastolic", name="check_systolic_greater_than_diastolic"),
    )

# class BloodPressureLog(Base):
#     __tablename__ = "bp_logs"

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

#     systolic = Column(Integer, nullable=False)     # e.g., 120
#     diastolic = Column(Integer, nullable=False)    # e.g., 80
#     pulse = Column(Integer, nullable=True)         # optional heart rate
#     notes = Column(String(500), nullable=True)     # optional notes

#     checked_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
#     created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

#     # Relationships
#     user = relationship("User", back_populates="bp_logs")

#     __table_args__ = (
#         CheckConstraint("systolic > 0 AND systolic < 300", name="check_systolic_range"),
#         CheckConstraint("diastolic > 0 AND diastolic < 200", name="check_diastolic_range"),
#         CheckConstraint("pulse IS NULL OR (pulse > 0 AND pulse < 250)", name="check_pulse_range"),
#         CheckConstraint("systolic > diastolic", name="check_systolic_greater_than_diastolic"),
#     )