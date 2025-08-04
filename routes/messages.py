import os
from database import get_db
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from models.chats import Chat
from crud.chats import (
    get_chat,
    get_chat_summary,
    set_chat_summary,
)

from models.users import User
from middlewares.auth import get_current_user

from schemas.messages import (
    MessageCreate,
    MessageResponse,
    Regenerate_Message,
)
from crud.messages import (
    get_message,
    get_summary,
    delete_message,
    delete_last_message,
    get_messages_by_chat,
    create_message_with_ai,
    get_last_user_message_by_chat,
)

load_dotenv()

router = APIRouter()

def _generate_response(
    db: Session,
    user: User,
    chat: Chat,
    request_text: str,
    message_context: str,
) -> MessageResponse:
    saved_message = create_message_with_ai(
        db,
        user.id,
        MessageCreate(
            chat_id=chat.id,
            request=request_text,
        ),
        message_context,
    )
    if isinstance(saved_message, dict) and "error" in saved_message:
        raise HTTPException(status_code=502, detail=saved_message["error"])

    db.commit()
    db.refresh(user)

    return MessageResponse(
        id=saved_message.id,
        chat_id=saved_message.chat_id,
        request=saved_message.request,
        response=saved_message.response,
        created_at=saved_message.created_at,
        updated_at=saved_message.updated_at,
    )


def _validate_request(current_user: User, request_text: str):
    if not current_user.id or not request_text:
        raise HTTPException(
            status_code=400,
            detail="User ID and request text are required.",
        )

@router.post("/regenerate", response_model=MessageResponse)
def send_message_regenerate(
    message_data: Regenerate_Message,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat = get_chat(db, message_data.chat_id)
    if chat is None or chat.user_id != current_user.id:
        raise HTTPException(
            status_code=404 if chat is None else 403,
            detail="Chat not found" if chat is None else "Not authorized",
        )

    request_text = get_last_user_message_by_chat(db, chat.id)
    message_context = get_chat_summary(db, chat.id)

    _validate_request(current_user, request_text)

    delete_last_message(db, chat.id)

    return _generate_response(
        db,
        current_user,
        chat,
        request_text,
        message_context,
    )


@router.post("", response_model=MessageResponse)
def send_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _validate_request(current_user, message_data.request)

    message_context = ""
    chat_id = message_data.chat_id

    if chat_id:
        message_context = get_summary(db, chat_id)
        set_chat_summary(db, chat_id, message_context)

    if not chat_id:
        new_chat = Chat(
            user_id=current_user.id,
            topic=message_data.request[:30],
            created_at=datetime.now(timezone.utc),
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)
        chat_id = new_chat.id

    chat = get_chat(db, chat_id)
    if chat is None or chat.user_id != current_user.id:
        raise HTTPException(
            status_code=404 if chat is None else 403,
            detail="Chat not found" if chat is None else "Not authorized",
        )

    response = _generate_response(
        db,
        current_user,
        chat,
        message_data.request,
        message_context,
    )

    db.commit()
    db.refresh(current_user)

    return response


@router.get("/{message_id}", response_model=MessageResponse)
def read_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_message = get_message(db, message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    db_chat = get_chat(db, db_message.chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if db_chat.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this chat"
        )

    return db_message


@router.delete("/{message_id}")
def delete_existing_message(
    message_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_message = get_message(db, message_id)
    if db_message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    db_chat = get_chat(db, db_message.chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if db_chat.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this chat"
        )

    deleted_message = delete_message(db, message_id)
    if deleted_message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}


@router.get("/chat/{chat_id}", response_model=list[MessageResponse])
def fetch_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_chat = get_chat(db, chat_id)
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    if db_chat.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this chat"
        )
    messages = get_messages_by_chat(db, chat_id)
    if not messages:
        raise HTTPException(status_code=404, detail="No messages found for this chat")
    return messages
