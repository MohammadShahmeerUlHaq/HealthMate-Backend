from config import settings
from dotenv import load_dotenv
from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import os
import google.generativeai as genai
from typing import Tuple
import json
import re

from models.messages import Message
from crud.chats import get_chat_summary
from crud.bp_logs import get_recent_bp_logs, get_logs_by_user_id, get_logs_by_date_range
from crud.bp_schedules import get_user_bp_schedules
from crud.sugar_logs import get_recent_sugar_logs, get_sugar_logs_by_user, get_sugar_logs_by_date_range
from crud.sugar_schedules import get_user_sugar_schedules
from crud.medications import get_user_medicines, get_user_medications
from crud.users import get_user

from schemas.messages import MessageCreate, MessagePair
from constants.systemPrompt import system_prompt

from langchain.chains.summarize import load_summarize_chain
from langchain_google_genai import ChatGoogleGenerativeAI as GoogleGenerativeAI
from langchain.prompts import SystemMessagePromptTemplate
from langchain.schema import Document

# Use the unified agent for Gemini 2.5 Flash + tool calling
from utilities.langchain_agent import run_langchain_agent

load_dotenv()

genai.configure(api_key=settings.GEMINI_API_KEY)

gemini_model = genai.GenerativeModel("models/gemini-2.5-flash")

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

def safe_serialize_response(response):
    if isinstance(response, (dict, list)):
        return json.dumps(response, default=str)
    return str(response)

def create_message_with_ai(db: Session, user_id: int, message: MessageCreate, message_context: str):
    try:
        user_message = message.request
        if message_context:
            user_message = f"[Previous context: {message_context}]\n{user_message}"
        # Use the unified agent (Gemini 2.5 Flash + tool calling)
        response = run_langchain_agent(user_message, db, user_id)
        user_message_obj = Message(
            response=safe_serialize_response(response),
            chat_id=message.chat_id,
            request=message.request,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(user_message_obj)
        db.commit()
        db.refresh(user_message_obj)
        return user_message_obj
    except Exception as e:
        db.rollback()
        print(f"DB Error: {e}")
        return {"error": "Internal server error"}

def summarize_conversation_incremental(messages: list, previous_summary: str) -> str:
    """Perform an incremental summary using Gemini 2.5 Flash."""
    if not messages:
        return previous_summary
    text_to_summarize = previous_summary + "\n" + "\n".join([
        f"User: {m.user}\nAI: {m.ai}" for m in messages
    ])
    docs = [Document(page_content=text_to_summarize)]
    llm = GoogleGenerativeAI(
        model="models/gemini-2.5-flash",
        google_api_key=os.environ.get("GEMINI_API_KEY"),
        temperature=0.2,
    )
    system_prompt_template = SystemMessagePromptTemplate.from_template(system_prompt)
    chain = load_summarize_chain(llm, chain_type="stuff")
    try:
        summary = chain.run(docs)
        return summary
    except Exception as e:
        print(f"Error summarizing conversation: {e}")
        return previous_summary

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