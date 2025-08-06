from fastapi import APIRouter, Depends, Query, Response
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
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import tempfile
from fpdf import FPDF
from .alerts import generate_alerts_route

router = APIRouter()

def daterange(start_date, end_date):
    """Generate date range from start_date to end_date inclusive"""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def calculate_medication_adherence(schedules, logs, start_date, end_date, log_date_field, schedule_id_field):
    """Calculate adherence based on schedules and logs"""
    total = 0
    adhered = 0
    
    # Create a lookup for logs by (day, schedule_id)
    logs_by_day_sched = {}
    for log in logs:
        log_date = getattr(log, log_date_field)
        if isinstance(log_date, datetime):
            log_day = log_date.date()
        else:
            log_day = log_date
        schedule_id = getattr(log, schedule_id_field)
        logs_by_day_sched[(log_day, schedule_id)] = log
    
    # Check each schedule for each day in the period
    for sched in schedules:
        day = start_date
        while day <= end_date:
            # Check if schedule is active on this day
            if sched.medication.start_date.date() <= day and (not sched.medication.end_date or sched.medication.end_date.date() >= day):
                total += 1
                if (day, sched.id) in logs_by_day_sched:
                    adhered += 1
            day += timedelta(days=1)
    
    return adhered, total

def calculate_adherence(schedules, logs, start_date, end_date, log_date_field, schedule_id_field):
    """Calculate adherence based on schedules and logs"""
    total = 0
    adhered = 0
    
    # Create a lookup for logs by (day, schedule_id)
    logs_by_day_sched = {}
    for log in logs:
        log_date = getattr(log, log_date_field)
        if isinstance(log_date, datetime):
            log_day = log_date.date()
        else:
            log_day = log_date
        schedule_id = getattr(log, schedule_id_field)
        logs_by_day_sched[(log_day, schedule_id)] = log
    
    # Check each schedule for each day in the period
    for sched in schedules:
        day = start_date
        while day <= end_date:
            # Check if schedule is active on this day
            if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
                total += 1
                if (day, sched.id) in logs_by_day_sched:
                    adhered += 1
            day += timedelta(days=1)
    
    return adhered, total

def plot_bp_chart(bp_logs):
    """Create a blood pressure chart with both systolic and diastolic, avoiding vertical lines from duplicate timestamps."""
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import io
    from collections import defaultdict
    from datetime import datetime, time

    plt.figure(figsize=(10, 4))

    if bp_logs:
        grouped = defaultdict(lambda: {"systolic": [], "diastolic": []})

        for log in bp_logs:
            log_time = log.checked_at if isinstance(log.checked_at, datetime) else datetime.combine(log.checked_at, time.min)
            log_time = log_time.replace(second=0, microsecond=0)  # Normalize
            grouped[log_time]["systolic"].append(log.systolic)
            grouped[log_time]["diastolic"].append(log.diastolic)

        # Sort by time
        sorted_items = sorted(grouped.items())
        dates = [dt for dt, _ in sorted_items]
        systolic_avg = [sum(values["systolic"]) / len(values["systolic"]) for _, values in sorted_items]
        diastolic_avg = [sum(values["diastolic"]) / len(values["diastolic"]) for _, values in sorted_items]

        plt.plot(dates, systolic_avg, marker='o', label='Systolic', linewidth=2, markersize=4, color='#ff7f0e')  # Orange
        plt.plot(dates, diastolic_avg, marker='s', label='Diastolic', linewidth=2, markersize=4, color='#2ca02c')  # Green
        plt.legend()

        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))

    plt.xlabel('Date')
    plt.ylabel('Blood Pressure (mmHg)')
    plt.title('Blood Pressure Trend')
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    return buf

def plot_sugar_chart(sugar_logs):
    """Create a sugar level line chart separated by type (e.g., FASTING, RANDOM)"""
    from collections import defaultdict
    from datetime import datetime, time
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import io

    plt.figure(figsize=(10, 4))

    # Use nested dict to group by type and datetime
    grouped = defaultdict(lambda: defaultdict(list))

    for log in sugar_logs:
        log_time = log.checked_at if isinstance(log.checked_at, datetime) else datetime.combine(log.checked_at, time.min)
        log_time = log_time.replace(second=0, microsecond=0)  # Normalize seconds/microseconds
        label = getattr(log.type, 'name', str(log.type))
        grouped[label][log_time].append(log.value)

    # Prepare cleaned data
    sugar_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    for idx, (label, times_dict) in enumerate(grouped.items()):
        sorted_items = sorted(times_dict.items())
        dates = [dt for dt, _ in sorted_items]
        values = [sum(vals) / len(vals) for _, vals in sorted_items]  # average values
        color = sugar_colors[idx % len(sugar_colors)]
        plt.plot(dates, values, marker='o', linewidth=2, markersize=4, label=label, color=color)

    plt.xlabel("Date")
    plt.ylabel("Sugar Level (mg/dL)")
    plt.title("Blood Sugar Trend")
    plt.legend()
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    return buf


def plot_adherence_chart(dates, adherence_percents):
    """Create an adherence bar chart with vertical bars"""
    plt.figure(figsize=(10, 4))
    if dates and adherence_percents:
        # For single day (Daily view), create one centered bar
        if len(dates) == 1:
            plt.bar([0], adherence_percents, width=0.4, alpha=0.7, color='#1f77b4')  # Single narrow bar
            plt.xticks([0], dates)
        else:
            # Use range indices for x-axis and set custom labels for multiple days
            x_pos = range(len(dates))
            plt.bar(x_pos, adherence_percents, width=0.6, alpha=0.7, color='#1f77b4')  # Consistent blue color
            plt.xticks(x_pos, dates)
    
    plt.xlabel('Date')
    plt.ylabel('Adherence (%)')
    plt.title('Daily Adherence')
    plt.ylim(0, 100)  # Set consistent Y-axis scale
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    buf.seek(0)
    return buf

def generate_pdf_report(user: User, bp_logs, sugar_logs, adherence_data, adherence_chart, bp_chart, sugar_chart, start_date, end_date):

    temp_files = []

    def add_chart(pdf, chart_file):
        temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
        temp_files.append(temp_path)
        try:
            with os.fdopen(temp_fd, 'wb') as tmp_file:
                tmp_file.write(chart_file.read())

            # Estimate image height (maintain aspect ratio if needed)
            chart_height = 75

            if pdf.get_y() + chart_height > 270:  # Avoid bottom margin cutoff
                pdf.add_page()
            
            pdf.image(temp_path, x=15, y=pdf.get_y(), w=180)
            pdf.ln(chart_height)  # Only move down by chart height
        except:
            os.close(temp_fd)


    try:
        pdf = FPDF()
        pdf.add_page()

        # --- HEADER ---
        pdf.image("static/healthmate_logo.png", x=10, y=8, w=25)  # Adjust path if needed
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "HEALTHMATE", ln=True, align="C")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 5, "YOUR WELLNESS COMPANION", ln=True, align="C")
        pdf.ln(10)

        # --- PATIENT INFO ---
        pdf.set_font("Arial", "", 11)
        pdf.cell(100, 7, f"Patient Name: {user.name}", ln=0)
        pdf.cell(90, 7, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
        pdf.cell(100, 7, f"Patient ID: {user.id}", ln=1)
        pdf.ln(5)

        # --- ADHERENCE SECTION ---
        pdf.set_font("Arial", "B", 13)
        pdf.cell(0, 10, "Medication Adherence", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 8, f"Overall adherence: {adherence_data.get('adherence_percent', 0):.1f}%", ln=True)
        add_chart(pdf, adherence_chart)

        # --- BLOOD PRESSURE SECTION ---
        if bp_logs:
            if pdf.get_y() > 200:  # Avoid bottom cutoff
                pdf.add_page()
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 10, "Blood Pressure Logs", ln=True)

            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 8, "Date", 1)
            pdf.cell(40, 8, "Time", 1)
            pdf.cell(50, 8, "Systolic (mmHg)", 1)
            pdf.cell(50, 8, "Diastolic (mmHg)", 1)
            pdf.ln()

            pdf.set_font("Arial", "", 10)
            for log in bp_logs[-10:]:
                pdf.cell(50, 8, log.checked_at.strftime("%Y-%m-%d"), 1)
                pdf.cell(40, 8, log.checked_at.strftime("%H:%M"), 1)
                pdf.cell(50, 8, str(log.systolic), 1, align="C")
                pdf.cell(50, 8, str(log.diastolic), 1, align="C")
                pdf.ln()
            pdf.ln()
            # pdf.cell(0, 10, "Blood Pressure Trend", ln=True)
            add_chart(pdf, bp_chart)

        # --- SUGAR SECTION ---
        if sugar_logs:
            if pdf.get_y() > 200:  # Avoid bottom cutoff
                pdf.add_page()
            pdf.set_font("Arial", "B", 13)
            pdf.cell(0, 10, "Blood Sugar Logs", ln=True)

            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 8, "Date", 1)
            pdf.cell(40, 8, "Time", 1)
            pdf.cell(50, 8, "Type", 1)
            pdf.cell(50, 8, "Value (mg/dL)", 1)
            pdf.ln()

            pdf.set_font("Arial", "", 10)
            for log in sugar_logs[-10:]:
                pdf.cell(50, 8, log.checked_at.strftime("%Y-%m-%d"), 1)
                pdf.cell(40, 8, log.checked_at.strftime("%H:%M"), 1)
                pdf.cell(50, 8, getattr(log.type, 'name', str(log.type)), 1)
                pdf.cell(50, 8, str(log.value), 1, align="C")
                pdf.ln()
            pdf.ln()
            # pdf.cell(0, 10, "Sugar Trend", ln=True)
            add_chart(pdf, sugar_chart)

        #Alerts Section
        # if alerts:
        #     if pdf.get_y() > 200:  # Avoid bottom cutoff
        #         pdf.add_page()
        #     pdf.set_font("Arial", "B", 13)
        #     pdf.cell(0, 10, "Alerts", ln=True)

        #     pdf.set_font("Arial", "B", 10)
        #     pdf.cell(50, 8, "Tag", 1)
        #     pdf.cell(40, 8, "Heading", 1)
        #     pdf.cell(50, 8, "Description", 1)
        #     pdf.cell(50, 8, "Date", 1)
        #     pdf.cell(50, 8, "Time", 1)
        #     pdf.ln()

        #     pdf.set_font("Arial", "", 10)
        #     for alert in alerts[-10:]:
        #         if alert["tag"]=="Emergency":
        #             pdf.cell(50, 8, str(alert["tag"]), 1, align="C")
        #             pdf.cell(50, 8, str(alert["heading"]), 1, align="C")
        #             pdf.cell(50, 8, str(alert["description"]), 1, align="C")
        #             pdf.cell(50, 8, alert["date"], 1)
        #             pdf.cell(40, 8, alert["time"], 1)
        #             pdf.ln()
        #     pdf.ln()
        
        # --- FOOTER ---
        pdf.ln()
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 10, "Automated Report", ln=True, align="R")

        pdf_bytes = pdf.output(dest='S').encode('latin1')
        buf = io.BytesIO(pdf_bytes)
        buf.seek(0)
        return buf

    finally:
        for temp_path in temp_files:
            try:
                os.remove(temp_path)
            except:
                pass


@router.post("")
def generate_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: InsightPeriod = Query(InsightPeriod.DAILY, description="Report period: daily, weekly, or monthly"),
    start_date: date = Query(None, description="Optional start date override (if not provided, automatically calculated based on period)")
):
    """Generate comprehensive health report with adherence data and charts"""
    
    # 1. Calculate date range automatically based on period (like frontend getDateRange)
    today = date.today()
    
    if start_date is None:
        # Auto-calculate start_date based on period (matching frontend logic)
        if period == InsightPeriod.DAILY:
            start_date = today  # Today only
            end_date = today
        elif period == InsightPeriod.WEEKLY:
            start_date = today - timedelta(days=6)  # Last 7 days
            end_date = today
        elif period == InsightPeriod.MONTHLY:
            start_date = today - timedelta(days=29)  # Last 30 days
            end_date = today
        else:
            return {"success": False, "error": "Unknown period."}
    else:
        # Use provided start_date and calculate end_date based on period
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

        # Ensure end_date doesn't go beyond today
        if end_date > today:
            end_date = today

    # 2. Query schedules and logs - Fixed to match alerts.py schema
    
    # Medication data
    medications = db.query(Medication).filter(
        Medication.user_id == current_user.id, 
        Medication.is_active == True
    ).all()
    
    med_schedules = []
    med_logs = []
    for med in medications:
        for sched in med.schedules:
            med_schedules.append(sched)
            # Get logs for this schedule in the date range
            sched_logs = db.query(MedicationLog).filter(
                MedicationLog.medication_schedule_id == sched.id,
                MedicationLog.scheduled_date >= start_date,
                MedicationLog.scheduled_date <= end_date
            ).all()
            med_logs.extend(sched_logs)

    # Blood Pressure data
    bp_schedules = db.query(BloodPressureSchedule).filter(
        BloodPressureSchedule.user_id == current_user.id, 
        BloodPressureSchedule.is_active == True
    ).all()
    
    bp_logs = db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
    BloodPressureSchedule.user_id == current_user.id,
    BloodPressureLog.checked_at >= datetime.combine(start_date, time.min),
    BloodPressureLog.checked_at <= datetime.combine(end_date, time.max)
    ).all()

    # Sugar data
    sugar_schedules = db.query(SugarSchedule).filter(
        SugarSchedule.user_id == current_user.id, 
        SugarSchedule.is_active == True
    ).all()
    
    sugar_logs = db.query(SugarLog).join(SugarSchedule).filter(
    SugarSchedule.user_id == current_user.id,
    SugarLog.checked_at >= datetime.combine(start_date, time.min),
    SugarLog.checked_at <= datetime.combine(end_date, time.max)
    ).all()

    # 3. Calculate adherence
    med_adhered, med_total = calculate_medication_adherence(
        med_schedules, med_logs, start_date, end_date, "scheduled_date", "medication_schedule_id"
    )
    bp_adhered, bp_total = calculate_adherence(
        bp_schedules, bp_logs, start_date, end_date, "checked_at", "schedule_id"
    )
    sugar_adhered, sugar_total = calculate_adherence(
        sugar_schedules, sugar_logs, start_date, end_date, "checked_at", "schedule_id"
    )
    
    total = med_total + bp_total + sugar_total
    adhered = med_adhered + bp_adhered + sugar_adhered
    adherence_percent = (adhered / total * 100) if total > 0 else 0

    # 4. Prepare data for daily adherence chart
    days = list(daterange(start_date, end_date))
    adherence_per_day = []
    
    for day in days:
        day_total = 0
        day_adhered = 0
        
        # Check medication adherence for this day
        for med in medications:
            for sched in med.schedules:
                if med.start_date.date() <= day and (not med.end_date or med.end_date.date() >= day):
                    day_total += 1
                    log = next((log for log in med_logs 
                              if log.scheduled_date == day and log.medication_schedule_id == sched.id), None)
                    if log and log.taken_at:
                        day_adhered += 1
        
        # Check BP adherence for this day
        for sched in bp_schedules:
            if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
                day_total += 1
                log = next((log for log in bp_logs 
                          if log.checked_at.date() == day and log.schedule_id == sched.id), None)
                if log:
                    day_adhered += 1
        
        # Check sugar adherence for this day
        for sched in sugar_schedules:
            if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
                day_total += 1
                log = next((log for log in sugar_logs 
                          if log.checked_at.date() == day and log.schedule_id == sched.id), None)
                if log:
                    day_adhered += 1
        
        day_adherence = (day_adhered / day_total * 100) if day_total > 0 else 0
        adherence_per_day.append((day, day_adherence))

    # 5. Generate charts
    try:
        # BP chart
        bp_chart = plot_bp_chart(bp_logs)
        
        # Sugar chart
        sugar_chart = plot_sugar_chart(sugar_logs)
        
        # Adherence chart
        adherence_chart = plot_adherence_chart(
            [d.strftime("%m/%d") for d, _ in adherence_per_day],
            [a for _, a in adherence_per_day]
        )

        # 6. Generate PDF
        adherence_data = {
            "adherence_percent": adherence_percent,
            "total_scheduled": total,
            "total_completed": adhered
        }

        # alerts = generate_alerts_route(db, current_user, period, start_date)
        
        pdf_buf = generate_pdf_report(
            current_user,
            # alerts["alerts"],
            bp_logs, sugar_logs, adherence_data, 
            adherence_chart, bp_chart, sugar_chart, 
            start_date, end_date
        )

        # 7. Return PDF response
        return Response(
            content=pdf_buf.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=health_report_{start_date}_{end_date}.pdf",
                "X-Adherence-Percent": f"{adherence_percent:.2f}"
            }
        )
        
    except Exception as e:
        return {"success": False, "error": f"Error generating report: {str(e)}"}

@router.get("/adherence")
def get_adherence_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: InsightPeriod = Query(InsightPeriod.DAILY, description="Report period: daily, weekly, or monthly"),
    start_date: date = Query(None, description="Optional start date override (if not provided, automatically calculated based on period)")
):
    """Return adherence summary with per-day adherence values for graphing."""

    # 1. Calculate date range automatically based on period (like frontend getDateRange)
    today = date.today()
    
    if start_date is None:
        # Auto-calculate start_date based on period (matching frontend logic)
        if period == InsightPeriod.DAILY:
            start_date = today  # Today only
            end_date = today
        elif period == InsightPeriod.WEEKLY:
            start_date = today - timedelta(days=6)  # Last 7 days
            end_date = today
        elif period == InsightPeriod.MONTHLY:
            start_date = today - timedelta(days=29)  # Last 30 days
            end_date = today
        else:
            return {"success": False, "error": "Unknown period."}
    else:
        # Use provided start_date and calculate end_date based on period
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

        # Ensure end_date doesn't go beyond today
        if end_date > today:
            end_date = today

    # 2. Query schedules and logs
    medications = db.query(Medication).filter(
        Medication.user_id == current_user.id,
        Medication.is_active == True
    ).all()

    med_schedules = []
    med_logs = []
    for med in medications:
        for sched in med.schedules:
            med_schedules.append(sched)
            sched_logs = db.query(MedicationLog).filter(
                MedicationLog.medication_schedule_id == sched.id,
                MedicationLog.scheduled_date >= start_date,
                MedicationLog.scheduled_date <= end_date
            ).all()
            med_logs.extend(sched_logs)

    bp_schedules = db.query(BloodPressureSchedule).filter(
        BloodPressureSchedule.user_id == current_user.id,
        BloodPressureSchedule.is_active == True
    ).all()

    bp_logs = db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
        BloodPressureSchedule.user_id == current_user.id,
        BloodPressureLog.checked_at >= datetime.combine(start_date, time.min),
        BloodPressureLog.checked_at <= datetime.combine(end_date, time.max)
    ).all()

    sugar_schedules = db.query(SugarSchedule).filter(
        SugarSchedule.user_id == current_user.id,
        SugarSchedule.is_active == True
    ).all()

    sugar_logs = db.query(SugarLog).join(SugarSchedule).filter(
        SugarSchedule.user_id == current_user.id,
        SugarLog.checked_at >= datetime.combine(start_date, time.min),
        SugarLog.checked_at <= datetime.combine(end_date, time.max)
    ).all()

    # 3. Calculate overall adherence
    med_adhered, med_total = calculate_medication_adherence(
        med_schedules, med_logs, start_date, end_date, "scheduled_date", "medication_schedule_id"
    )
    bp_adhered, bp_total = calculate_adherence(
        bp_schedules, bp_logs, start_date, end_date, "checked_at", "schedule_id"
    )
    sugar_adhered, sugar_total = calculate_adherence(
        sugar_schedules, sugar_logs, start_date, end_date, "checked_at", "schedule_id"
    )

    total = med_total + bp_total + sugar_total
    adhered = med_adhered + bp_adhered + sugar_adhered
    adherence_percent = (adhered / total * 100) if total > 0 else 0

    # 4. Calculate daily adherence array for the graph
    days = list(daterange(start_date, end_date))
    daily_adherence = []
    
    for day in days:
        day_total = 0
        day_adhered = 0

        # Medication adherence per day
        for med in medications:
            for sched in med.schedules:
                if med.start_date.date() <= day and (not med.end_date or med.end_date.date() >= day):
                    day_total += 1
                    log = next((log for log in med_logs
                                if log.scheduled_date == day and log.medication_schedule_id == sched.id), None)
                    if log and log.taken_at:
                        day_adhered += 1

        # Blood Pressure adherence per day
        for sched in bp_schedules:
            if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
                day_total += 1
                log = next((log for log in bp_logs
                            if log.checked_at.date() == day and log.schedule_id == sched.id), None)
                if log:
                    day_adhered += 1

        # Sugar adherence per day
        for sched in sugar_schedules:
            if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
                day_total += 1
                log = next((log for log in sugar_logs
                            if log.checked_at.date() == day and log.schedule_id == sched.id), None)
                if log:
                    day_adhered += 1

        daily_percent = (day_adhered / day_total * 100) if day_total > 0 else 0
        daily_adherence.append({
            "date": day.strftime("%Y-%m-%d"),
            "adherence_percent": round(daily_percent, 2),
            "completed": day_adhered,
            "scheduled": day_total
        })

    return {
        "success": True,
        "start_date": start_date,
        "end_date": end_date,
        "total_scheduled": total,
        "total_completed": adhered,
        "adherence_percent": round(adherence_percent, 2),
        "breakdown": {
            "medication": {"scheduled": med_total, "completed": med_adhered},
            "blood_pressure": {"scheduled": bp_total, "completed": bp_adhered},
            "sugar": {"scheduled": sugar_total, "completed": sugar_adhered},
        },
        "daily_adherence": daily_adherence  # Array for graphing
    }

# from fastapi import APIRouter, Depends, Query, Response
# from sqlalchemy.orm import Session
# from database import get_db
# from datetime import date, datetime, timedelta, time
# from middlewares.auth import get_current_user
# from models.users import User
# from models.medications import Medication
# from models.medication_schedules import MedicationSchedule
# from models.medication_logs import MedicationLog
# from models.bp_schedules import BloodPressureSchedule
# from models.bp_logs import BloodPressureLog
# from models.sugar_schedules import SugarSchedule
# from models.sugar_logs import SugarLog
# from models.insights import InsightPeriod
# from typing import List, Dict, Any
# import io
# import matplotlib
# matplotlib.use('Agg')
# import matplotlib.pyplot as plt
# import os
# import tempfile
# from fpdf import FPDF
# from .alerts import generate_alerts_route

# router = APIRouter()

# def daterange(start_date, end_date):
#     """Generate date range from start_date to end_date inclusive"""
#     for n in range(int((end_date - start_date).days) + 1):
#         yield start_date + timedelta(n)

# def calculate_medication_adherence(schedules, logs, start_date, end_date, log_date_field, schedule_id_field):
#     """Calculate adherence based on schedules and logs"""
#     total = 0
#     adhered = 0
    
#     # Create a lookup for logs by (day, schedule_id)
#     logs_by_day_sched = {}
#     for log in logs:
#         log_date = getattr(log, log_date_field)
#         if isinstance(log_date, datetime):
#             log_day = log_date.date()
#         else:
#             log_day = log_date
#         schedule_id = getattr(log, schedule_id_field)
#         logs_by_day_sched[(log_day, schedule_id)] = log
    
#     # Check each schedule for each day in the period
#     for sched in schedules:
#         day = start_date
#         while day <= end_date:
#             # Check if schedule is active on this day
#             if sched.medication.start_date.date() <= day and (not sched.medication.end_date or sched.medication.end_date.date() >= day):
#                 total += 1
#                 if (day, sched.id) in logs_by_day_sched:
#                     adhered += 1
#             day += timedelta(days=1)
    
#     return adhered, total

# def calculate_adherence(schedules, logs, start_date, end_date, log_date_field, schedule_id_field):
#     """Calculate adherence based on schedules and logs"""
#     total = 0
#     adhered = 0
    
#     # Create a lookup for logs by (day, schedule_id)
#     logs_by_day_sched = {}
#     for log in logs:
#         log_date = getattr(log, log_date_field)
#         if isinstance(log_date, datetime):
#             log_day = log_date.date()
#         else:
#             log_day = log_date
#         schedule_id = getattr(log, schedule_id_field)
#         logs_by_day_sched[(log_day, schedule_id)] = log
    
#     # Check each schedule for each day in the period
#     for sched in schedules:
#         day = start_date
#         while day <= end_date:
#             # Check if schedule is active on this day
#             if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
#                 total += 1
#                 if (day, sched.id) in logs_by_day_sched:
#                     adhered += 1
#             day += timedelta(days=1)
    
#     return adhered, total

# def plot_bp_chart(bp_logs):
#     """Create a blood pressure chart with both systolic and diastolic"""
#     plt.figure(figsize=(10, 4))
    
#     if bp_logs:
#         # Convert to proper datetime objects for plotting
#         # Already mostly correct, only ensure datetime formatting:
#         dates = [log.checked_at if isinstance(log.checked_at, datetime) else datetime.combine(log.checked_at, time.min) for log in bp_logs]

#         # dates = [log.checked_at if isinstance(log.checked_at, datetime) 
#         #         else datetime.combine(log.checked_at, time.min) for log in bp_logs]
#         systolic = [log.systolic for log in bp_logs]
#         diastolic = [log.diastolic for log in bp_logs]
        
#         plt.plot(dates, systolic, marker='o', label='Systolic', linewidth=2, markersize=4)
#         plt.plot(dates, diastolic, marker='s', label='Diastolic', linewidth=2, markersize=4)
#         plt.legend()
#         import matplotlib.dates as mdates
#         plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
#         plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))

    
#     plt.xlabel('Date')
#     plt.ylabel('Blood Pressure (mmHg)')
#     plt.title('Blood Pressure Trend')
#     plt.xticks(rotation=45)
#     plt.tight_layout()
    
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=150)
#     plt.close()
#     buf.seek(0)
#     return buf

# def plot_sugar_chart(sugar_logs):
#     """Create a sugar level line chart separated by type (e.g., FASTING, RANDOM)"""
#     from collections import defaultdict
#     plt.figure(figsize=(10, 4))

#     # Group values by type
#     data_by_type = defaultdict(lambda: {"dates": [], "values": []})

#     for log in sugar_logs:
#         log_time = log.checked_at if isinstance(log.checked_at, datetime) else datetime.combine(log.checked_at, time.min)
#         label = getattr(log.type, 'name', str(log.type))
#         data_by_type[label]["dates"].append(log_time)
#         data_by_type[label]["values"].append(log.value)

#     # Plot each group with a different color and label
#     for idx, (label, data) in enumerate(data_by_type.items()):
#         plt.plot(data["dates"], data["values"], marker='o', linewidth=2, markersize=4, label=label)

#     plt.xlabel("Date")
#     plt.ylabel("Sugar Level (mg/dL)")
#     plt.title("Blood Sugar Trend")
#     plt.legend()
#     import matplotlib.dates as mdates
#     plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
#     plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=1))
#     plt.xticks(rotation=45)
#     plt.tight_layout()

#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=150)
#     plt.close()
#     buf.seek(0)
#     return buf

# def plot_adherence_chart(dates, adherence_percents):
#     """Create an adherence bar chart"""
#     plt.figure(figsize=(10, 4))
#     if dates and adherence_percents:
#         # Use range indices for x-axis and set custom labels
#         x_pos = range(len(dates))
#         plt.bar(x_pos, adherence_percents, alpha=0.7)
#         plt.xticks(x_pos, dates)
#     plt.xlabel('Date')
#     plt.ylabel('Adherence (%)')
#     plt.title('Daily Adherence')
#     plt.ylim(0, 100)
#     plt.xticks(rotation=45)
#     plt.tight_layout()
    
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=150)
#     plt.close()
#     buf.seek(0)
#     return buf

# def generate_pdf_report(user: User, bp_logs, sugar_logs, adherence_data, adherence_chart, bp_chart, sugar_chart, start_date, end_date):

#     temp_files = []

#     def add_chart(pdf, chart_file):
#         temp_fd, temp_path = tempfile.mkstemp(suffix='.png')
#         temp_files.append(temp_path)
#         try:
#             with os.fdopen(temp_fd, 'wb') as tmp_file:
#                 tmp_file.write(chart_file.read())

#             # Estimate image height (maintain aspect ratio if needed)
#             chart_height = 75

#             if pdf.get_y() + chart_height > 270:  # Avoid bottom margin cutoff
#                 pdf.add_page()
            
#             pdf.image(temp_path, x=15, y=pdf.get_y(), w=180)
#             pdf.ln(chart_height)  # Only move down by chart height
#         except:
#             os.close(temp_fd)


#     try:
#         pdf = FPDF()
#         pdf.add_page()

#         # --- HEADER ---
#         pdf.image("static/healthmate_logo.png", x=10, y=8, w=25)  # Adjust path if needed
#         pdf.set_font("Arial", "B", 16)
#         pdf.cell(0, 10, "HEALTHMATE", ln=True, align="C")
#         pdf.set_font("Arial", "", 12)
#         pdf.cell(0, 5, "YOUR WELLNESS COMPANION", ln=True, align="C")
#         pdf.ln(10)

#         # --- PATIENT INFO ---
#         pdf.set_font("Arial", "", 11)
#         pdf.cell(100, 7, f"Patient Name: {user.name}", ln=0)
#         pdf.cell(90, 7, f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=1)
#         pdf.cell(100, 7, f"Patient ID: {user.id}", ln=1)
#         pdf.ln(5)

#         # --- ADHERENCE SECTION ---
#         pdf.set_font("Arial", "B", 13)
#         pdf.cell(0, 10, "Medication Adherence", ln=True)
#         pdf.set_font("Arial", "", 11)
#         pdf.cell(0, 8, f"Overall adherence: {adherence_data.get('adherence_percent', 0):.1f}%", ln=True)
#         add_chart(pdf, adherence_chart)

#         # --- BLOOD PRESSURE SECTION ---
#         if bp_logs:
#             if pdf.get_y() > 200:  # Avoid bottom cutoff
#                 pdf.add_page()
#             pdf.set_font("Arial", "B", 13)
#             pdf.cell(0, 10, "Blood Pressure Logs", ln=True)

#             pdf.set_font("Arial", "B", 10)
#             pdf.cell(50, 8, "Date", 1)
#             pdf.cell(40, 8, "Time", 1)
#             pdf.cell(50, 8, "Systolic (mmHg)", 1)
#             pdf.cell(50, 8, "Diastolic (mmHg)", 1)
#             pdf.ln()

#             pdf.set_font("Arial", "", 10)
#             for log in bp_logs[-10:]:
#                 pdf.cell(50, 8, log.checked_at.strftime("%Y-%m-%d"), 1)
#                 pdf.cell(40, 8, log.checked_at.strftime("%H:%M"), 1)
#                 pdf.cell(50, 8, str(log.systolic), 1, align="C")
#                 pdf.cell(50, 8, str(log.diastolic), 1, align="C")
#                 pdf.ln()
#             pdf.ln()
#             # pdf.cell(0, 10, "Blood Pressure Trend", ln=True)
#             add_chart(pdf, bp_chart)

#         # --- SUGAR SECTION ---
#         if sugar_logs:
#             if pdf.get_y() > 200:  # Avoid bottom cutoff
#                 pdf.add_page()
#             pdf.set_font("Arial", "B", 13)
#             pdf.cell(0, 10, "Blood Sugar Logs", ln=True)

#             pdf.set_font("Arial", "B", 10)
#             pdf.cell(50, 8, "Date", 1)
#             pdf.cell(40, 8, "Time", 1)
#             pdf.cell(50, 8, "Type", 1)
#             pdf.cell(50, 8, "Value (mg/dL)", 1)
#             pdf.ln()

#             pdf.set_font("Arial", "", 10)
#             for log in sugar_logs[-10:]:
#                 pdf.cell(50, 8, log.checked_at.strftime("%Y-%m-%d"), 1)
#                 pdf.cell(40, 8, log.checked_at.strftime("%H:%M"), 1)
#                 pdf.cell(50, 8, getattr(log.type, 'name', str(log.type)), 1)
#                 pdf.cell(50, 8, str(log.value), 1, align="C")
#                 pdf.ln()
#             pdf.ln()
#             # pdf.cell(0, 10, "Sugar Trend", ln=True)
#             add_chart(pdf, sugar_chart)

#         #Alerts Section
#         # if alerts:
#         #     if pdf.get_y() > 200:  # Avoid bottom cutoff
#         #         pdf.add_page()
#         #     pdf.set_font("Arial", "B", 13)
#         #     pdf.cell(0, 10, "Alerts", ln=True)

#         #     pdf.set_font("Arial", "B", 10)
#         #     pdf.cell(50, 8, "Tag", 1)
#         #     pdf.cell(40, 8, "Heading", 1)
#         #     pdf.cell(50, 8, "Description", 1)
#         #     pdf.cell(50, 8, "Date", 1)
#         #     pdf.cell(50, 8, "Time", 1)
#         #     pdf.ln()

#         #     pdf.set_font("Arial", "", 10)
#         #     for alert in alerts[-10:]:
#         #         if alert["tag"]=="Emergency":
#         #             pdf.cell(50, 8, str(alert["tag"]), 1, align="C")
#         #             pdf.cell(50, 8, str(alert["heading"]), 1, align="C")
#         #             pdf.cell(50, 8, str(alert["description"]), 1, align="C")
#         #             pdf.cell(50, 8, alert["date"], 1)
#         #             pdf.cell(40, 8, alert["time"], 1)
#         #             pdf.ln()
#         #     pdf.ln()
        
#         # --- FOOTER ---
#         pdf.ln()
#         pdf.set_font("Arial", "", 11)
#         pdf.cell(0, 10, "Automated Report", ln=True, align="R")

#         pdf_bytes = pdf.output(dest='S').encode('latin1')
#         buf = io.BytesIO(pdf_bytes)
#         buf.seek(0)
#         return buf

#     finally:
#         for temp_path in temp_files:
#             try:
#                 os.remove(temp_path)
#             except:
#                 pass


# @router.post("")
# def generate_report(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     period: InsightPeriod = Query(InsightPeriod.DAILY, description="Report period: daily, weekly, or monthly"),
#     start_date: date = Query(date.today(), description="Start date for the report period (defaults to today)")
# ):
#     """Generate comprehensive health report with adherence data and charts"""
    
#     # 1. Calculate end_date based on period
#     if period == InsightPeriod.DAILY:
#         end_date = start_date
#     elif period == InsightPeriod.WEEKLY:
#         end_date = start_date + timedelta(days=6)
#     elif period == InsightPeriod.MONTHLY:
#         if start_date.month == 12:
#             end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
#         else:
#             end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
#     else:
#         return {"success": False, "error": "Unknown period."}

#     today = date.today()
#     if end_date > today:
#         end_date = today

#     # 2. Query schedules and logs - Fixed to match alerts.py schema
    
#     # Medication data
#     medications = db.query(Medication).filter(
#         Medication.user_id == current_user.id, 
#         Medication.is_active == True
#     ).all()
    
#     med_schedules = []
#     med_logs = []
#     for med in medications:
#         for sched in med.schedules:
#             med_schedules.append(sched)
#             # Get logs for this schedule in the date range
#             sched_logs = db.query(MedicationLog).filter(
#                 MedicationLog.medication_schedule_id == sched.id,
#                 MedicationLog.scheduled_date >= start_date,
#                 MedicationLog.scheduled_date <= end_date
#             ).all()
#             med_logs.extend(sched_logs)

#     # Blood Pressure data
#     bp_schedules = db.query(BloodPressureSchedule).filter(
#         BloodPressureSchedule.user_id == current_user.id, 
#         BloodPressureSchedule.is_active == True
#     ).all()
    
#     bp_logs = db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
#     BloodPressureSchedule.user_id == current_user.id,
#     BloodPressureLog.checked_at >= datetime.combine(start_date, time.min),
#     BloodPressureLog.checked_at <= datetime.combine(end_date, time.max)
#     ).all()

#     # Sugar data
#     sugar_schedules = db.query(SugarSchedule).filter(
#         SugarSchedule.user_id == current_user.id, 
#         SugarSchedule.is_active == True
#     ).all()
    
#     sugar_logs = db.query(SugarLog).join(SugarSchedule).filter(
#     SugarSchedule.user_id == current_user.id,
#     SugarLog.checked_at >= datetime.combine(start_date, time.min),
#     SugarLog.checked_at <= datetime.combine(end_date, time.max)
#     ).all()

#     # 3. Calculate adherence
#     med_adhered, med_total = calculate_medication_adherence(
#         med_schedules, med_logs, start_date, end_date, "scheduled_date", "medication_schedule_id"
#     )
#     bp_adhered, bp_total = calculate_adherence(
#         bp_schedules, bp_logs, start_date, end_date, "checked_at", "schedule_id"
#     )
#     sugar_adhered, sugar_total = calculate_adherence(
#         sugar_schedules, sugar_logs, start_date, end_date, "checked_at", "schedule_id"
#     )
    
#     total = med_total + bp_total + sugar_total
#     adhered = med_adhered + bp_adhered + sugar_adhered
#     adherence_percent = (adhered / total * 100) if total > 0 else 0

#     # 4. Prepare data for daily adherence chart
#     days = list(daterange(start_date, end_date))
#     adherence_per_day = []
    
#     for day in days:
#         day_total = 0
#         day_adhered = 0
        
#         # Check medication adherence for this day
#         for med in medications:
#             for sched in med.schedules:
#                 if med.start_date.date() <= day and (not med.end_date or med.end_date.date() >= day):
#                     day_total += 1
#                     log = next((log for log in med_logs 
#                               if log.scheduled_date == day and log.medication_schedule_id == sched.id), None)
#                     if log and log.taken_at:
#                         day_adhered += 1
        
#         # Check BP adherence for this day
#         for sched in bp_schedules:
#             if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
#                 day_total += 1
#                 log = next((log for log in bp_logs 
#                           if log.checked_at.date() == day and log.schedule_id == sched.id), None)
#                 if log:
#                     day_adhered += 1
        
#         # Check sugar adherence for this day
#         for sched in sugar_schedules:
#             if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
#                 day_total += 1
#                 log = next((log for log in sugar_logs 
#                           if log.checked_at.date() == day and log.schedule_id == sched.id), None)
#                 if log:
#                     day_adhered += 1
        
#         day_adherence = (day_adhered / day_total * 100) if day_total > 0 else 0
#         adherence_per_day.append((day, day_adherence))

#     # 5. Generate charts
#     try:
#         # BP chart
#         bp_chart = plot_bp_chart(bp_logs)
        
#         # Sugar chart
#         sugar_chart = plot_sugar_chart(sugar_logs)
        
#         # Adherence chart
#         adherence_chart = plot_adherence_chart(
#             [d.strftime("%m/%d") for d, _ in adherence_per_day],
#             [a for _, a in adherence_per_day]
#         )

#         # 6. Generate PDF
#         adherence_data = {
#             "adherence_percent": adherence_percent,
#             "total_scheduled": total,
#             "total_completed": adhered
#         }

#         # alerts = generate_alerts_route(db, current_user, period, start_date)
        
#         pdf_buf = generate_pdf_report(
#             current_user,
#             # alerts["alerts"],
#             bp_logs, sugar_logs, adherence_data, 
#             adherence_chart, bp_chart, sugar_chart, 
#             start_date, end_date
#         )

#         # 7. Return PDF response
#         return Response(
#             content=pdf_buf.read(),
#             media_type="application/pdf",
#             headers={
#                 "Content-Disposition": f"attachment; filename=health_report_{start_date}_{end_date}.pdf",
#                 "X-Adherence-Percent": f"{adherence_percent:.2f}"
#             }
#         )
        
#     except Exception as e:
#         return {"success": False, "error": f"Error generating report: {str(e)}"}

# @router.get("/adherence")
# def get_adherence_summary(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
#     period: InsightPeriod = Query(InsightPeriod.DAILY, description="Report period: daily, weekly, or monthly"),
#     start_date: date = Query(date.today(), description="Start date for the report period (defaults to today)")
# ):
#     """Return adherence summary with per-day adherence values for graphing."""

#     # 1. Determine end_date based on period
#     if period == InsightPeriod.DAILY:
#         end_date = start_date
#     elif period == InsightPeriod.WEEKLY:
#         end_date = start_date + timedelta(days=6)
#     elif period == InsightPeriod.MONTHLY:
#         if start_date.month == 12:
#             end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
#         else:
#             end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
#     else:
#         return {"success": False, "error": "Unknown period."}

#     # 2. Query schedules and logs
#     medications = db.query(Medication).filter(
#         Medication.user_id == current_user.id,
#         Medication.is_active == True
#     ).all()

#     med_schedules = []
#     med_logs = []
#     for med in medications:
#         for sched in med.schedules:
#             med_schedules.append(sched)
#             sched_logs = db.query(MedicationLog).filter(
#                 MedicationLog.medication_schedule_id == sched.id,
#                 MedicationLog.scheduled_date >= start_date,
#                 MedicationLog.scheduled_date <= end_date
#             ).all()
#             med_logs.extend(sched_logs)

#     bp_schedules = db.query(BloodPressureSchedule).filter(
#         BloodPressureSchedule.user_id == current_user.id,
#         BloodPressureSchedule.is_active == True
#     ).all()

#     bp_logs = db.query(BloodPressureLog).join(BloodPressureSchedule).filter(
#         BloodPressureSchedule.user_id == current_user.id,
#         BloodPressureLog.checked_at >= datetime.combine(start_date, time.min),
#         BloodPressureLog.checked_at <= datetime.combine(end_date, time.max)
#     ).all()

#     sugar_schedules = db.query(SugarSchedule).filter(
#         SugarSchedule.user_id == current_user.id,
#         SugarSchedule.is_active == True
#     ).all()

#     sugar_logs = db.query(SugarLog).join(SugarSchedule).filter(
#         SugarSchedule.user_id == current_user.id,
#         SugarLog.checked_at >= datetime.combine(start_date, time.min),
#         SugarLog.checked_at <= datetime.combine(end_date, time.max)
#     ).all()

#     # 3. Calculate overall adherence
#     med_adhered, med_total = calculate_medication_adherence(
#         med_schedules, med_logs, start_date, end_date, "scheduled_date", "medication_schedule_id"
#     )
#     bp_adhered, bp_total = calculate_adherence(
#         bp_schedules, bp_logs, start_date, end_date, "checked_at", "schedule_id"
#     )
#     sugar_adhered, sugar_total = calculate_adherence(
#         sugar_schedules, sugar_logs, start_date, end_date, "checked_at", "schedule_id"
#     )

#     total = med_total + bp_total + sugar_total
#     adhered = med_adhered + bp_adhered + sugar_adhered
#     adherence_percent = (adhered / total * 100) if total > 0 else 0

#     # 4. Calculate daily adherence array for the graph
#     days = list(daterange(start_date, end_date))
#     daily_adherence = []
    
#     for day in days:
#         day_total = 0
#         day_adhered = 0

#         # Medication adherence per day
#         for med in medications:
#             for sched in med.schedules:
#                 if med.start_date.date() <= day and (not med.end_date or med.end_date.date() >= day):
#                     day_total += 1
#                     log = next((log for log in med_logs
#                                 if log.scheduled_date == day and log.medication_schedule_id == sched.id), None)
#                     if log and log.taken_at:
#                         day_adhered += 1

#         # Blood Pressure adherence per day
#         for sched in bp_schedules:
#             if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
#                 day_total += 1
#                 log = next((log for log in bp_logs
#                             if log.checked_at.date() == day and log.schedule_id == sched.id), None)
#                 if log:
#                     day_adhered += 1

#         # Sugar adherence per day
#         for sched in sugar_schedules:
#             if sched.start_date <= day and (not sched.end_date or sched.end_date >= day):
#                 day_total += 1
#                 log = next((log for log in sugar_logs
#                             if log.checked_at.date() == day and log.schedule_id == sched.id), None)
#                 if log:
#                     day_adhered += 1

#         daily_percent = (day_adhered / day_total * 100) if day_total > 0 else 0
#         daily_adherence.append({
#             "date": day.strftime("%Y-%m-%d"),
#             "adherence_percent": round(daily_percent, 2),
#             "completed": day_adhered,
#             "scheduled": day_total
#         })

#     return {
#         "success": True,
#         "start_date": start_date,
#         "end_date": end_date,
#         "total_scheduled": total,
#         "total_completed": adhered,
#         "adherence_percent": round(adherence_percent, 2),
#         "breakdown": {
#             "medication": {"scheduled": med_total, "completed": med_adhered},
#             "blood_pressure": {"scheduled": bp_total, "completed": bp_adhered},
#             "sugar": {"scheduled": sugar_total, "completed": sugar_adhered},
#         },
#         "daily_adherence": daily_adherence  # Array for graphing
#     }