from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from datetime import date, datetime, timedelta, time
from middlewares.auth import get_current_user
from models.users import User
from models.medications import Medication
from models.medication_schedules import MedicationSchedule
from models.medication_logs import MedicationLog
from models.bp_schedules import BloodPressureSchedule
from models.bp_logs import BloodPressureLog
from models.sugar_schedules import SugarSchedule
from models.sugar_logs import SugarLog
from models.insights import InsightPeriod
from typing import List, Dict, Any

router = APIRouter()

@router.post("")
def generate_alerts_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: InsightPeriod = Query(InsightPeriod.DAILY, description="Alert period: daily, weekly, or monthly"),
    start_date: date = Query(date.today(), description="Start date for the alert period (defaults to today)")
):
    if period == InsightPeriod.DAILY:
        end_date = start_date
    elif period == InsightPeriod.WEEKLY:
        end_date = start_date + timedelta(days=6)
    elif period == InsightPeriod.MONTHLY:
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    else:
        return {"success": False, "error": "Unknown period."}

    alerts = []
    # --- Medication Missed Dose Alerts ---
    medications = db.query(Medication).filter(Medication.user_id == current_user.id, Medication.is_active == True).all()
    for med in medications:
        med_name = med.medicine.name if hasattr(med, 'medicine') and med.medicine else f"Medicine ID {med.medicine_id}"
        for sched in med.schedules:
            day = start_date
            while day <= end_date:
                if med.start_date.date() <= day and (not med.end_date or med.end_date.date() >= day):
                    scheduled_dt = datetime.combine(day, sched.time)
                    if scheduled_dt < datetime.now():
                        log = db.query(MedicationLog).filter_by(medication_schedule_id=sched.id, scheduled_date=day).first()
                        if not log or not log.taken_at:
                            if day == date.today():
                                desc = f"You missed your {sched.dosage_instruction or ''} {med_name} dose scheduled at {sched.time.strftime('%I:%M %p')} on {day.strftime('%m/%d/%y')}. Please take it now if within 2 hours."
                            else:
                                desc = f"You missed your {sched.dosage_instruction or ''} {med_name} dose scheduled at {sched.time.strftime('%I:%M %p')} on {day.strftime('%m/%d/%y')}."
                            alerts.append({
                                "tag": "REMINDER",
                                "heading": "Medicine Reminder: Missed Dose Alert",
                                "description": desc,
                                "date": str(day),
                                "time": str(sched.time)
                            })
                day += timedelta(days=1)

    # --- BP Missed Check & Out-of-Range Alerts ---
    bp_schedules = db.query(BloodPressureSchedule).filter(BloodPressureSchedule.user_id == current_user.id, BloodPressureSchedule.is_active == True).all()
    for sched in bp_schedules:
        day = start_date
        while day <= end_date:
            if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
                scheduled_dt = datetime.combine(day, sched.time)
                if scheduled_dt < datetime.now():
                    log = db.query(BloodPressureLog).filter(BloodPressureLog.schedule_id == sched.id, BloodPressureLog.checked_at >= datetime.combine(day, time.min), BloodPressureLog.checked_at <= datetime.combine(day, time.max)).first()
                    if not log:
                        alerts.append({
                            "tag": "REMINDER",
                            "heading": "BP Reminder: Missed BP Check",
                            "description": f"You missed your blood pressure check scheduled at {sched.time.strftime('%I:%M %p')} on {day.strftime('%m/%d/%y')}. Please check as soon as possible.",
                            "date": str(day),
                            "time": str(sched.time)
                        })
                    else:
                        # Determine BP alert type
                        high_systolic = current_user.bp_systolic_max is not None and log.systolic > current_user.bp_systolic_max
                        low_systolic = current_user.bp_systolic_min is not None and log.systolic < current_user.bp_systolic_min
                        high_diastolic = current_user.bp_diastolic_max is not None and log.diastolic > current_user.bp_diastolic_max
                        low_diastolic = current_user.bp_diastolic_min is not None and log.diastolic < current_user.bp_diastolic_min
                        heading = None
                        desc = None
                        if (high_systolic or high_diastolic) and (low_systolic or low_diastolic):
                            heading = "Emergency Alert: High and Low BP Detected"
                            desc = f"BP Reading: {log.systolic}/{log.diastolic} detected at {log.checked_at.strftime('%I:%M %p')}. Systolic or diastolic is both above and below safe range. Seek immediate medical attention."
                        elif high_systolic or high_diastolic:
                            heading = "Emergency Alert: High BP Detected"
                            desc = f"BP Reading: {log.systolic}/{log.diastolic} detected at {log.checked_at.strftime('%I:%M %p')}. High blood pressure detected. Immediate attention advised."
                        elif low_systolic or low_diastolic:
                            heading = "Emergency Alert: Low BP Detected"
                            desc = f"BP Reading: {log.systolic}/{log.diastolic} detected at {log.checked_at.strftime('%I:%M %p')}. Low blood pressure detected. Immediate attention advised."
                        if heading:
                            alerts.append({
                                "tag": "EMERGENCY",
                                "heading": heading,
                                "description": desc,
                                "date": log.checked_at.strftime('%m/%d/%y'),
                                "time": log.checked_at.strftime('%I:%M %p')
                            })
            day += timedelta(days=1)

    # --- Sugar Missed Check & Out-of-Range Alerts ---
    sugar_schedules = db.query(SugarSchedule).filter(SugarSchedule.user_id == current_user.id, SugarSchedule.is_active == True).all()
    for sched in sugar_schedules:
        day = start_date
        while day <= end_date:
            if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
                scheduled_dt = datetime.combine(day, sched.time)
                if scheduled_dt < datetime.now():
                    log = db.query(SugarLog).filter(SugarLog.schedule_id == sched.id, SugarLog.checked_at >= datetime.combine(day, time.min), SugarLog.checked_at <= datetime.combine(day, time.max)).first()
                    if not log:
                        alerts.append({
                            "tag": "REMINDER",
                            "heading": "Sugar Reminder: Missed Sugar Check",
                            "description": f"You missed your sugar check scheduled at {sched.time.strftime('%I:%M %p')} on {day.strftime('%m/%d/%y')}. Please check as soon as possible.",
                            "date": str(day),
                            "time": str(sched.time)
                        })
                    else:
                        # Fasting or random sugar high/low logic
                        if log.type.name.lower() == "fasting":
                            high = current_user.sugar_fasting_max is not None and log.value > current_user.sugar_fasting_max
                            low = current_user.sugar_fasting_min is not None and log.value < current_user.sugar_fasting_min
                            if high:
                                heading = "Emergency Alert: High Fasting Sugar Detected"
                                desc = f"Fasting sugar reading: {log.value} detected at {log.checked_at.strftime('%I:%M %p')} on {log.checked_at.strftime('%m/%d/%y')}. High fasting sugar detected. Immediate attention advised."
                            elif low:
                                heading = "Emergency Alert: Low Fasting Sugar Detected"
                                desc = f"Fasting sugar reading: {log.value} detected at {log.checked_at.strftime('%I:%M %p')} on {log.checked_at.strftime('%m/%d/%y')}. Low fasting sugar detected. Immediate attention advised."
                            else:
                                heading = None
                                desc = None
                        else:
                            high = current_user.sugar_random_max is not None and log.value > current_user.sugar_random_max
                            low = current_user.sugar_random_min is not None and log.value < current_user.sugar_random_min
                            if high:
                                heading = "Emergency Alert: High Random Sugar Detected"
                                desc = f"Random sugar reading: {log.value} detected at {log.checked_at.strftime('%I:%M %p')} on {log.checked_at.strftime('%m/%d/%y')}. High random sugar detected. Immediate attention advised."
                            elif low:
                                heading = "Emergency Alert: Low Random Sugar Detected"
                                desc = f"Random sugar reading: {log.value} detected at {log.checked_at.strftime('%I:%M %p')} on {log.checked_at.strftime('%m/%d/%y')}. Low random sugar detected. Immediate attention advised."
                            else:
                                heading = None
                                desc = None
                        if heading:
                            alerts.append({
                                "tag": "EMERGENCY",
                                "heading": heading,
                                "description": desc,
                                "date": log.checked_at.strftime('%m/%d/%y'),
                                "time": log.checked_at.strftime('%I:%M %p')
                            })
            day += timedelta(days=1)

    # Sort alerts: EMERGENCY first, then REMINDER; within each, by date desc, time desc, then type
    def alert_sort_key(alert):
        tag_priority = 0 if alert.get("tag") == "EMERGENCY" else 1
        from datetime import datetime as dt
        try:
            dt_obj = dt.strptime(f"{alert['date']} {alert['time']}", "%m/%d/%y %I:%M %p")
            ts = -dt_obj.timestamp()
        except Exception:
            ts = float('inf')  # fallback: push unparsable dates to the end
        return (tag_priority, ts, alert.get("type", ""))

    alerts.sort(key=alert_sort_key)

    return {"success": True, "alerts": alerts}
