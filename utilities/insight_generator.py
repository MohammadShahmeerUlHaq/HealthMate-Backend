from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
import json
import re
from models.insights import Insight, InsightPeriod
from crud.bp_logs import get_logs_by_date as get_bp_logs
from crud.sugar_logs import get_sugar_logs_by_date
from crud.medication_logs import get_logs_by_date as get_med_logs
from crud.bp_schedules import get_user_bp_schedules
from crud.sugar_schedules import get_user_sugar_schedules
from crud.medications import get_user_medications
from utilities.gemini_client import generate_gemini_response
from sqlalchemy.exc import IntegrityError
import tenacity
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

EXPECTED_INSIGHT_JSON_KEYS = [
    "smart_recommendations",
    "adherence",
    "vital_sign_patterns",
    "unusual_spikes"
]

DANGEROUS_RECOMMENDATION_KEYWORDS = [
    "stop taking", "discontinue medication", "diagnose yourself", "self-prescribe",
    "cure diabetes", "cure hypertension", "replace insulin", "ignore doctor"
]

# --- Main generate_daily_insight function with all guardrails and updated error handling ---

def build_gemini_prompt(period, start_date, end_date, bp_schedules_str, sugar_schedules_str, med_schedules_str, bp_logs_str, sugar_logs_str, med_logs_str):
    """
    Build the Gemini prompt for insight generation, including schedules and logs, and period-awareness.
    """
    period_label = period.value.title()
    date_range_str = f"{start_date} to {end_date}" if start_date != end_date else f"{start_date}"
    return f"""
You are an AI health assistant for HealthMate, focused on managing chronic conditions like diabetes and hypertension.
Based on the following {period_label.lower()} health logs and schedules for {date_range_str}, generate a concise {period_label.lower()} health insight.

Blood Pressure Schedules:\n{bp_schedules_str}

Sugar Schedules:\n{sugar_schedules_str}

Medication Schedules:\n{med_schedules_str}

**Instructions for Response Format (Strictly Adhere):**
1.  **Title:** Start your response with "Title:" followed by a concise, informative title (e.g., "{period_label} Health Summary for {date_range_str}").
2.  **Summary:** On a new line, start with "Summary:" followed by a brief overall summary of the {period_label.lower()} health, highlighting key observations from the logs.
3.  **JSON Block:** Provide a valid JSON object enclosed in triple backticks (```json...```). This JSON must contain the following top-level keys, each with a list of relevant observations or recommendations:
    -   "smart_recommendations": actionable general health advice based on the provided logs.
    -   "adherence": observations on medication and schedule adherence for the {period_label.lower()}.
    -   "vital_sign_patterns": analysis of blood pressure and/or sugar trends or significant readings.
    -   "unusual_spikes": identification of any abnormal or concerning readings that stand out.
    Ensure all JSON values are valid strings, numbers, or boolean types. Do NOT include any non-JSON content inside the ```json...``` block.

**Important Safety Guidelines:**
* **DO NOT** make medical diagnoses or claim to cure diseases.
* **DO NOT** prescribe specific medications or advise on medication dosages.
* **DO NOT** tell the user to stop or change their prescribed medications without consulting a doctor.
* Focus on observations from the data, general healthy lifestyle recommendations (e.g., "stay hydrated", "monitor readings"), and adherence tracking.
* Remind the user to consult a healthcare professional for personalized medical advice.

Blood Pressure Logs:\n{bp_logs_str}

Sugar Logs:\n{sugar_logs_str}

Medication Logs:\n{med_logs_str}

Remember to provide insights relevant to managing chronic conditions.
"""


def generate_insight(db: Session, user_id: int, period: InsightPeriod, start_date: date):
    """
    Generates a health insight for a user for the given period (daily, weekly, monthly), returns the parsed data (does NOT save to DB).
    The end_date is calculated based on the period.
    """
    # Calculate end_date based on period
    if period == InsightPeriod.DAILY:
        end_date = start_date
    elif period == InsightPeriod.WEEKLY:
        end_date = start_date + timedelta(days=6)
    elif period == InsightPeriod.MONTHLY:
        # Get last day of the month
        if start_date.month == 12:
            end_date = start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
    else:
        raise ValueError(f"Unknown period: {period}")


    # Fetch logs for the period
    if period == InsightPeriod.DAILY:
        bp_logs = get_bp_logs(db, user_id, start_date)
        sugar_logs = get_sugar_logs_by_date(db, user_id, start_date)
        med_logs = get_med_logs(db, user_id, start_date)
    else:
        # Use date range functions for weekly/monthly
        from crud.bp_logs import get_logs_by_date_range as get_bp_logs_by_range
        from crud.sugar_logs import get_sugar_logs_by_date_range as get_sugar_logs_by_range
        from crud.medication_logs import get_logs_by_date_range as get_med_logs_by_range
        # For BP logs, use datetime range
        bp_logs = get_bp_logs_by_range(db, user_id, datetime.combine(start_date, datetime.min.time()), datetime.combine(end_date, datetime.max.time()))
        sugar_logs = get_sugar_logs_by_range(db, user_id, start_date, end_date)
        med_logs = get_med_logs_by_range(db, user_id, start_date, end_date)

    # Schedules logic remains unchanged
    bp_schedules = get_user_bp_schedules(db, user_id)
    sugar_schedules = get_user_sugar_schedules(db, user_id)
    medications = get_user_medications(db, user_id)

    # Format BP schedules concisely
    def format_bp_schedules():
        if not bp_schedules:
            return "No BP schedules."
        return "\n".join(
            f"- {s.time.strftime('%I:%M %p')} ({s.start_date.strftime('%Y-%m-%d')} to {s.end_date.strftime('%Y-%m-%d')})"
            for s in bp_schedules if s.is_active and s.start_date <= end_date and (s.end_date or end_date) >= start_date
        ) or "No BP schedules."

    # Format sugar schedules concisely
    def format_sugar_schedules():
        if not sugar_schedules:
            return "No sugar schedules."
        return "\n".join(
            f"- {s.time.strftime('%I:%M %p')} ({s.start_date.strftime('%Y-%m-%d')} to {s.end_date.strftime('%Y-%m-%d')})"
            for s in sugar_schedules if s.is_active and s.start_date <= end_date and (s.end_date or end_date) >= start_date
        ) or "No sugar schedules."

    # Format medication schedules concisely
    def format_medication_schedules():
        if not medications:
            return "No medication schedules."
        lines = []
        for med in medications:
            med_name = f"{med.medicine.name} {med.medicine.strength}"
            scheds = [
                f"{s.time.strftime('%I:%M %p')}{f' ({s.dosage_instruction})' if s.dosage_instruction else ''}"
                for s in med.schedules
            ]
            if scheds:
                lines.append(f"- {med_name}: {', '.join(scheds)}")
        return "\n".join(lines) or "No medication schedules."

    # Format logs into string
    def format_bp():
        if not bp_logs:
            return "No blood pressure readings."
        return "\n".join(
            f"- {log.checked_at.strftime('%Y-%m-%d %I:%M %p')}: {log.systolic}/{log.diastolic} (Pulse: {log.pulse})"
            for log in bp_logs
        )

    def format_sugar():
        if not sugar_logs:
            return "No sugar readings."
        return "\n".join(
            f"- {log.checked_at.strftime('%Y-%m-%d %I:%M %p')} ({log.type.value}): {log.value} mg/dL"
            for log in sugar_logs
        )

    def format_meds():
        if not med_logs:
            return "No medication logs."
        return "\n".join(
            f"- {log.medication_schedule.medication.medicine.name} ({'Taken' if log.taken_at else 'Missed'})"
            for log in med_logs
        )

    # Compose Gemini prompt with schedules and period
    prompt = build_gemini_prompt(
        period,
        start_date,
        end_date,
        format_bp_schedules(),
        format_sugar_schedules(),
        format_medication_schedules(),
        format_bp(),
        format_sugar(),
        format_meds()
    )

    print(prompt)

    # Call Gemini with retry logic (unchanged)
    gemini_output = ""
    try:
        gemini_output = generate_gemini_response(prompt)
    except (GoogleAPIError, tenacity.RetryError, ValueError) as e:
        print(f"❌ Failed to get a valid Gemini response after retries for user {user_id} for {period.value} period {start_date} to {end_date}: {e}")
        import traceback
        traceback.print_exc()
        return None

    # --- Guardrail: Check for empty response (if it somehow slipped through or was initially empty) ---
    if not gemini_output:
        print(f"❌ Gemini output was unexpectedly empty for user {user_id} for {period.value} period {start_date} to {end_date} after retries. Cannot generate insight.")
        return None

    # Parsing and validation logic (unchanged, but use start_date/end_date/period)
    title = f"{period.value.title()} Health Insight"
    summary = "No detailed summary provided by AI."
    json_data = {key: [] for key in EXPECTED_INSIGHT_JSON_KEYS}

    try:
        # --- Guardrail: Robust Parsing of Title and Summary using Regex ---
        title_match = re.search(r"^Title:\s*(.*)$", gemini_output, re.MULTILINE | re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            print(f"⚠️ Gemini output missing 'Title:' line for user {user_id} for {period.value} period {start_date} to {end_date}. Using default.")

        summary_match = re.search(r"^Summary:\s*(.*)$", gemini_output, re.MULTILINE | re.IGNORECASE)
        if summary_match:
            summary = summary_match.group(1).strip()
        else:
            print(f"⚠️ Gemini output missing 'Summary:' line for user {user_id} for {period.value} period {start_date} to {end_date}. Using default.")

        # --- Guardrail: Extract and Validate JSON Block using Regex ---
        json_block_match = re.search(r"```json\s*(\{.*?\})\s*```", gemini_output, re.DOTALL)
        if not json_block_match:
            raise ValueError("Gemini output did not contain a valid JSON block enclosed in ```json...```.")

        json_raw = json_block_match.group(1).strip()
        json_data = json.loads(json_raw) # This will raise json.JSONDecodeError for invalid JSON

        # --- Guardrail: Validate JSON Structure and Expected Keys ---
        if not isinstance(json_data, dict):
            raise ValueError("Parsed JSON is not a dictionary.")
        for key in EXPECTED_INSIGHT_JSON_KEYS:
            if key not in json_data or not isinstance(json_data[key], list):
                # Ensure the key exists and its value is a list
                print(f"⚠️ JSON missing expected key '{key}' or its value is not a list. Initializing as empty list.")
                json_data[key] = [] # Set to empty list to prevent downstream errors
            else:
                # --- Contextual Guardrail: Check for Dangerous Recommendations (for smart_recommendations key) ---
                if key == "smart_recommendations":
                    filtered_recommendations = []
                    for rec in json_data[key]:
                        is_dangerous = False
                        rec_lower = rec.lower()
                        for keyword in DANGEROUS_RECOMMENDATION_KEYWORDS:
                            if keyword in rec_lower:
                                print(f"❌ Dangerous keyword '{keyword}' found in recommendation: '{rec}'. Filtering out.")
                                is_dangerous = True
                                break
                        if not is_dangerous:
                            filtered_recommendations.append(rec)
                    json_data[key] = filtered_recommendations
                    if not json_data[key]:
                        print(f"⚠️ 'smart_recommendations' list became empty after filtering for user {user_id} for {period.value} period {start_date} to {end_date}. Adding generic advice.")
                        json_data[key].append("Continue to monitor your health logs and consult your healthcare provider for personalized advice.")


        # # --- Contextual Guardrail: Add Medical Disclaimer to JSON data ---
        # json_data["medical_disclaimer"] = MEDICAL_DISCLAIMER
        
        # Instead of saving, return the data
        return {
            "user_id": user_id,
            "period": period,
            "start_date": start_date,
            "end_date": end_date,
            "title": title,
            "summary": summary,
            "json_data": json.dumps(json_data)
        }
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed for user {user_id} for {period.value} period {start_date} to {end_date}: {e}")
        return None
    except ValueError as e:
        print(f"❌ Gemini output format/structure validation failed for user {user_id} for {period.value} period {start_date} to {end_date}: {e}")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred during insight generation for user {user_id} for {period.value} period {start_date} to {end_date}: {e}")
        import traceback
        traceback.print_exc()
        return None

# Saving function remains as before
def save_insight_to_db(db, user_id, period, start_date, end_date, title, summary, json_data):
    """
    Saves a daily health insight to the database.
    """
    try:
        insight = Insight(
            user_id=user_id,
            period=period,
            start_date=start_date,
            end_date=end_date,
            title=title,
            summary=summary,
            json_data=json_data,
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        print(f"✅ Insight saved for user {user_id} on {start_date}")
        return insight
    except IntegrityError as e:
        db.rollback()
        print(f"⚠️ IntegrityError: Possibly duplicate entry for user {user_id} on {start_date}: {e}")
        return None
    except Exception as e:
        db.rollback()
        print(f"❌ An unexpected error occurred during saving insight for user {user_id} on {start_date}: {e}")
        import traceback
        traceback.print_exc()
        return None

# New function to generate and save
def generate_and_save_insight(db: Session, user_id: int, period: InsightPeriod, start_date: date):
    """
    Calls generate_daily_insight, then saves the result to the database if generation succeeded.
    Returns the saved Insight object or None.
    """
    existing = db.query(Insight).filter_by(
        user_id=user_id,
        period=period,
        start_date=start_date
    ).first()
    if existing:
        print(f"ℹ️ Insight for user {user_id} for {period.value} period starting {start_date} already exists. Skipping.")
        return None
    insight_data = generate_insight(db, user_id, period, start_date)
    if not insight_data:
        return None
    return save_insight_to_db(
        db=db,
        user_id=insight_data["user_id"],
        period=insight_data["period"],
        start_date=insight_data["start_date"],
        end_date=insight_data["end_date"],
        title=insight_data["title"],
        summary=insight_data["summary"],
        json_data=insight_data["json_data"]
    )
