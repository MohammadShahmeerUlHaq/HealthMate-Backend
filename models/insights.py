import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time, ForeignKey, 
    Enum, Text, Float, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base

class InsightPeriod(enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Insight(Base):
    __tablename__ = "insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    period = Column(Enum(InsightPeriod), nullable=False, index=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    
    title = Column(String(200), nullable=False)           # Brief title for the insight
    summary = Column(Text, nullable=False)                # Human-readable summary for user
    json_data = Column(Text, nullable=True)               # JSON string with graphs, breakdowns, scores
    
    # Metadata
    version = Column(String(10), default="1.0", nullable=False)  # For future insight format changes
    generated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="insights")

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_insight_date_order"),
        UniqueConstraint('user_id', 'period', 'start_date', name='unique_user_period_insight'),
    )