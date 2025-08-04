from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from models.insights import Insight, InsightPeriod

def get_insight_by_period_and_date(db: Session, user_id: int, period: InsightPeriod, start_date: date) -> Optional[Insight]:
    return db.query(Insight).filter_by(
        user_id=user_id,
        period=period,
        start_date=start_date
    ).first()
