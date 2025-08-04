from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from crud.chats import (
    create_chat,
    get_chat,
    update_chat,
    delete_chat,
    get_chats_by_user,
)
from schemas.chats import ChatCreate, ChatUpdate, ChatResponse
from middlewares.auth import get_current_user
from models.users import User

router = APIRouter()


@router.post("", response_model=ChatResponse)
def create_new_chat(
    chat: ChatCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_chat(db, chat, current_user)


@router.get("/{chat_id}", response_model=ChatResponse)
def read_chat(
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
    return db_chat


@router.put("/{chat_id}", response_model=ChatResponse)
def update_existing_chat(
    chat_id: int,
    chat: ChatUpdate,
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
    updated_chat = update_chat(db, chat_id, chat)
    if updated_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return updated_chat


@router.delete("/{chat_id}")
def delete_existing_chat(
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
    deleted_chat = delete_chat(db, chat_id)
    if deleted_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}


@router.get("", response_model=list[ChatResponse])
def fetch_chats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all chats corresponding to a user ID."""
    chats = get_chats_by_user(db, current_user.id)
    if not chats:
        raise HTTPException(status_code=404, detail="No chats found for this user")
    return chats
