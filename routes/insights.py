from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from utilities.insight_generator import generate_insight
from datetime import date, timedelta
from middlewares.auth import get_current_user
from models.users import User
from crud.insights import get_insight_by_period_and_date
from models.insights import InsightPeriod
from tasks.scheduler import generate_insights
from utilities.insight_generator import generate_and_save_insight

router = APIRouter()

@router.post("/run-insight-scheduler")
def generate_insight_route(
    period: InsightPeriod = Query(InsightPeriod.DAILY, description="Insight period: daily, weekly, or monthly")
):
    generate_insights(period)

@router.get("")
def get_insight_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: InsightPeriod = Query(InsightPeriod.DAILY, description="Insight period: daily, weekly, or monthly"),
    start_date: date = Query((date.today() - timedelta(days=1)), description="Start date for the insight period (defaults to yesterday)")
):
    insight_data = get_insight_by_period_and_date(db, current_user.id, period, start_date)
    if not insight_data:
        insight_data = generate_and_save_insight(db, current_user.id, period, start_date)
    if not insight_data:
        return {"success": False, "error": "Could not generate insight (no data)."}
    return {"success": True, "insight": insight_data}

# @router.post("")
# def generate_insight_route(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     period: InsightPeriod = Query(InsightPeriod.DAILY, description="Insight period: daily, weekly, or monthly"),
#     start_date: date = Query((date.today() - timedelta(days=1)), description="Start date for the insight period (defaults to yesterday)")
# ):
#     insight_data = get_insight_by_period_and_date(db, current_user.id, period, start_date)
#     if not insight_data:
#         insight_data = generate_insight(db, current_user.id, period, start_date)
#     if not insight_data:
#         return {"success": False, "error": "Could not generate insight (no data)."}
#     generate_and_save_insight(db, current_user.id, period, start_date)
#     return {"success": True, "insight": insight_data}

# @router.get("")
# def get_insight_route(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     period: InsightPeriod = Query(InsightPeriod.DAILY, description="Insight period: daily, weekly, or monthly"),
#     start_date: date = Query((date.today() - timedelta(days=1)), description="Start date for the insight period (defaults to yesterday)")
# ):
#     insight = get_insight_by_period_and_date(db, current_user.id, period, start_date)
#     return {"insight": insight}
