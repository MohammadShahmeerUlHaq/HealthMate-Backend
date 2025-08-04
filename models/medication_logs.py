import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class MedicationLog(Base):
    __tablename__ = "medication_logs"

    id = Column(Integer, primary_key=True, index=True)
    medication_schedule_id = Column(Integer, ForeignKey("medication_schedules.id"), nullable=False, index=True)
    
    scheduled_date = Column(Date, nullable=False, index=True)  # Date (e.g., 2025-06-18)

    taken_at = Column(DateTime(timezone=True), nullable=True)                # When they actually took it (optional)
    notes = Column(String(500), nullable=True)                # Optional notes from user

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # scheduled_time = Column(Time, nullable=False)         # Expected time for dose (e.g., 08:30)
    # taken = Column(Boolean, default=False, nullable=False)    # Whether patient confirmed it
    
    # Relationships
    medication_schedule = relationship("MedicationSchedule", back_populates="logs")

    __table_args__ = (
        UniqueConstraint('medication_schedule_id', 'scheduled_date', 
                        name='unique_medication_schedule'),
    )