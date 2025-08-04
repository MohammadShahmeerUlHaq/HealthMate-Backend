import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    strength = Column(String(50), nullable=False)  # e.g., "500mg", "2.5ml", "0.25mg"
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    medication_list = relationship("Medication", back_populates="medicine")

    __table_args__ = (
        UniqueConstraint('name', 'strength', name='unique_medicine_strength'),
        CheckConstraint("LENGTH(name) > 0", name="check_medicine_name_not_empty"),
        CheckConstraint("LENGTH(strength) > 0", name="check_strength_not_empty"),
    )