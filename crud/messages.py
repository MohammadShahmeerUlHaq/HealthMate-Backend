from config import settings
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import os
import google.generativeai as genai
from typing import Tuple

from models.messages import Message
from crud.chats import get_chat_summary
from crud.bp_logs import get_recent_bp_logs, get_logs_by_user_id, get_logs_by_date_range
from crud.bp_schedules import get_user_bp_schedules
from crud.sugar_logs import get_recent_sugar_logs, get_sugar_logs_by_user, get_sugar_logs_by_date_range
from crud.sugar_schedules import get_user_sugar_schedules
from crud.medications import get_user_medicines, get_user_medications
from crud.users import get_user
import json
import re

from schemas.messages import MessageCreate, MessagePair
from constants.systemPrompt import system_prompt

load_dotenv()

genai.configure(api_key=settings.GEMINI_API_KEY)

gemini_model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-1.5-pro"

class LLMResponseError(Exception):
    pass

def get_llm_response(message: str, system_message: str) -> Tuple[str, int]:
    prompt = system_message + '\n\nUser: ' + message
    try:
        response = gemini_model.generate_content(prompt)
        content = response.text
        return content
    except Exception as e:
        print(f"Error while calling Gemini API: {e}")
        raise LLMResponseError(str(e))

# # Tool registry: map tool names to functions
# TOOL_REGISTRY = {
#     "get_recent_bp_logs": get_recent_bp_logs,
#     "get_logs_by_user_id": get_logs_by_user_id,
#     "get_logs_by_date_range": get_logs_by_date_range,
#     "get_user_bp_schedules": get_user_bp_schedules,
#     "get_recent_sugar_logs": get_recent_sugar_logs,
#     "get_sugar_logs_by_user": get_sugar_logs_by_user,
#     "get_sugar_logs_by_date_range": get_sugar_logs_by_date_range,
#     "get_user_sugar_schedules": get_user_sugar_schedules,
#     "get_user_medicines": get_user_medicines,
#     "get_user_medications": get_user_medications,
#     "get_user": get_user,
# }

# def build_tool_prompt(user_message, tool_registry):
#     tool_descriptions = []
#     for name, func in tool_registry.items():
#         doc = func.__doc__ or ""
#         tool_descriptions.append(f"- {name}: {doc}")
#     tool_list = "\n".join(tool_descriptions)
#     return (
#         f"You are a health assistant. You have access to the following tools:\n"
#         f"{tool_list}\n\n"
#         "If you need to answer a question that requires data, respond with:\n"
#         "TOOL_CALL: {\"name\": \"<tool_name>\", \"args\": {...}}\n"
#         "If you have enough information, answer directly.\n"
#         f"User: {user_message}"
#     )

# def try_parse_tool_call(llm_response):
#     match = re.search(r'TOOL_CALL:\s*(\{.*\})', llm_response)
#     if match:
#         try:
#             return json.loads(match.group(1))
#         except Exception:
#             return None
#     return None

# def tool_calling_agent(db, user_id, user_message):
#     prompt = build_tool_prompt(user_message, TOOL_REGISTRY)
#     llm_response = gemini_model.generate_content(prompt)
#     tool_call = try_parse_tool_call(llm_response.text)
#     if tool_call:
#         tool_func = TOOL_REGISTRY.get(tool_call["name"])
#         if not tool_func:
#             return f"Sorry, I don't have a tool called {tool_call['name']}."
#         tool_args = tool_call.get("args", {})
#         tool_args["user_id"] = user_id  # Always inject user_id
#         # Try to call the tool, handle errors
#         try:
#             tool_result = tool_func(db=db, **tool_args)
#         except Exception as e:
#             return f"There was an error calling the tool: {e}"
#         followup_prompt = (
#             f"User asked: {user_message}\n"
#             f"Tool called: {tool_call['name']}({tool_args})\n"
#             f"Tool result: {tool_result}\n"
#             "Please answer conversationally."
#         )
#         final_response = gemini_model.generate_content(followup_prompt)
#         return final_response.text
#     else:
#         return llm_response.text

# # Replace create_message_with_ai with the tool-calling agent
# def create_message_with_ai(db: Session, user_id: int, message: MessageCreate, message_context: str):
#     # Optionally, you can add message_context to the prompt if you want to preserve chat history
#     user_message = message.request
#     if message_context:
#         user_message = f"[Previous context: {message_context}]\n{user_message}"
#     # Add user_id context for the AI
#     user_message = f"[user_id: {user_id}]\n" + user_message
#     response = tool_calling_agent(db, user_id, user_message)
#     user_message_obj = Message(
#         response=response,
#         chat_id=message.chat_id,
#         request=message.request,
#         created_at=datetime.now(timezone.utc),
#         updated_at=datetime.now(timezone.utc),
#     )
#     db.add(user_message_obj)
#     db.commit()
#     db.refresh(user_message_obj)
#     return user_message_obj

def create_message_with_ai(db: Session, user_id: int, message: MessageCreate, message_context: str):
    try:
        system_message = system_prompt

        medicines = get_user_medicines(db, user_id)
        bp_logs = get_recent_bp_logs(db, user_id, limit=4)
        sugar_logs = get_recent_sugar_logs(db, user_id, limit=4)

        # Format context parts
        context_parts = []

        if medicines:
            med_names = ', '.join([f"{med.name} ({med.strength})" for med in medicines])
            print(f"Current medications: {med_names}.")
            context_parts.append(f"Current medications: {med_names}.")

        if bp_logs:
            formatted_bp = ', '.join([
                f"{bp.checked_at.strftime('%b %d')}: {bp.systolic}/{bp.diastolic} mmHg"
                for bp in bp_logs
            ])
            print(f"Last 4 blood pressure readings: {formatted_bp}.")
            context_parts.append(f"Last 4 blood pressure readings: {formatted_bp}.")

        if sugar_logs:
            formatted_sugar = ', '.join([
                f"{sugar.checked_at.strftime('%b %d')}: {sugar.value} mg/dL"
                for sugar in sugar_logs
            ])
            print(f"Last 4 sugar level readings: {formatted_sugar}.")
            context_parts.append(f"Last 4 sugar level readings: {formatted_sugar}.")

        if context_parts:
            print(context_parts)
            system_message += '\n\n**Patient Summary**:\n' + '\n'.join(context_parts)

        if message_context:
            system_message += (
                '\nThe following is a summary of the previous conversation to maintain context:\n' + message_context + "\nPlease avoid repeating questions or greetings. Continue from where we left off."
            )

        print(system_message)

        # Get Gemini Response
        response = get_llm_response(message.request, system_message)

        user_message = Message(
            response=response,
            chat_id=message.chat_id,
            request=message.request,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        return user_message
    except LLMResponseError as e:
        return {"error": f"LLM call failed: {e}"}, 0
    except Exception as e:
        db.rollback()
        print(f"DB Error: {e}")
        return {"error": "Internal server error"}, 0


def summarize_conversation_incremental(messages: list, previous_summary: str) -> Tuple[str, int]:
    """Perform an incremental summary using Gemini."""
    if not messages:
        return previous_summary

    last_message = messages[-1]
    new_content = (
        f"Previous Summary:\n{previous_summary}\n\n"
        f"New Message:\nUser: {last_message.user}\nAI: {last_message.ai}"
    )
    try:
        response = gemini_model.generate_content(new_content + '\n\nPlease summarize the conversation succinctly:')
        updated_summary = response.text
        return updated_summary
    except Exception as e:
        print(f"Error summarizing conversation: {e}")
        return previous_summary, 0


def get_message(db: Session, message_id: int) -> Message:
    """Retrieve a message from the DB by ID."""
    return db.query(Message).filter(Message.id == message_id).first()


def delete_message(db: Session, message_id: int) -> Message:
    """Delete a message from the DB by ID."""
    db_message = db.query(Message).filter(Message.id == message_id).first()
    if db_message:
        db.delete(db_message)
        db.commit()
    return db_message


def get_messages_by_chat(db: Session, chat_id: int) -> list:
    """Retrieve all messages for a specific chat."""
    return db.query(Message).filter(Message.chat_id == chat_id).all()


def get_last_n_message_pairs(
    db: Session, chat_id: int, n: int = 5
) -> list[MessagePair]:
    rows = (
        db.query(Message.request, Message.response)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .limit(n)
        .all()
    )[::-1]

    return [MessagePair(user=row.request, ai=row.response) for row in rows]


def get_summary(db: Session, chat_id: int) -> str:
    messages = get_last_n_message_pairs(db, chat_id, 1)
    summary = get_chat_summary(db, chat_id)
    summary = summarize_conversation_incremental(messages, summary)
    return summary


def get_last_user_message_by_chat(db: Session, chat_id: int) -> str:
    row = (
        db.query(Message.request)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .first()
    )

    if row and row.request:
        return row.request

    raise HTTPException(status_code=404, detail="No messages found for this chat.")


def delete_last_message(db: Session, chat_id: int):
    last_message = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.desc())
        .first()
    )

    if not last_message:
        return False

    db.delete(last_message)
    db.commit()

    return True