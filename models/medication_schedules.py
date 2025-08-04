import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False, index=True)
    time = Column(Time, nullable=False)  # e.g., 08:30:00
    dosage_instruction = Column(String(200), nullable=True)  # e.g., "1 tablet", "5ml"
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    medication = relationship("Medication", back_populates="schedules")
    logs = relationship("MedicationLog", back_populates="medication_schedule", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('medication_id', 'time', name='unique_medication_time'),
        # CheckConstraint("LENGTH(dosage_instruction) > 0", name="check_dosage_not_empty"),
    )