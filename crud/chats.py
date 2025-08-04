from sqlalchemy.orm import Session
from models.chats import Chat
from schemas.chats import ChatCreate, ChatUpdate


def create_chat(db: Session, chat_data: ChatCreate, current_user):
    chat = Chat(user_id=current_user.id, topic=chat_data.topic)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def get_chat(db: Session, chat_id: int):
    return db.query(Chat).filter(Chat.id == chat_id).first()


def get_chat_summary(db: Session, chat_id: int) -> str:
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    return chat.summary if chat and chat.summary else ""


def set_chat_summary(db: Session, chat_id: int, summary: str):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        if summary is not None:
            chat.summary = summary
        db.commit()
        db.refresh(chat)
    return chat


def update_chat(db: Session, chat_id: int, chat_data: ChatUpdate):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        if chat_data.topic is not None:
            chat.topic = chat_data.topic
        db.commit()
        db.refresh(chat)
    return chat


def delete_chat(db: Session, chat_id: int):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat:
        db.delete(chat)
        db.commit()
    return chat


def get_chats_by_user(db: Session, user_id: int):
    return (
        db.query(Chat)
        .filter(Chat.user_id == user_id)
        .order_by(Chat.created_at.desc())
        .all()
    )
