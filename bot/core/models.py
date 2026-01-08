from sqlalchemy import BigInteger, String, Boolean, ForeignKey, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from datetime import datetime
from bot.core.database import Base

class Chat(Base):
    __tablename__ = "guard_chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    settings: Mapped["ChatSettings"] = relationship(back_populates="chat", uselist=False, cascade="all, delete-orphan")
    filters: Mapped[list["Filter"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    logs: Mapped[list["Log"]] = relationship(back_populates="chat", cascade="all, delete-orphan")

class ChatSettings(Base):
    __tablename__ = "guard_chat_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("guard_chats.id"), unique=True)
    
    language: Mapped[str] = mapped_column(String, default="ru")
    strict_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    log_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    delete_delay: Mapped[int] = mapped_column(Integer, default=0) # Seconds
    ignore_admins: Mapped[bool] = mapped_column(Boolean, default=True)

    chat: Mapped["Chat"] = relationship(back_populates="settings")

class Filter(Base):
    __tablename__ = "guard_filters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("guard_chats.id"))
    
    filter_type: Mapped[str] = mapped_column(String) # regex, link, caps, etc.
    pattern: Mapped[str] = mapped_column(Text, nullable=True) # The regex or keyword
    action: Mapped[str] = mapped_column(String, default="delete") # delete, mute, ban
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    chat: Mapped["Chat"] = relationship(back_populates="filters")

class Log(Base):
    __tablename__ = "guard_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("guard_chats.id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    action: Mapped[str] = mapped_column(String)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chat: Mapped["Chat"] = relationship(back_populates="logs")

class AdminCache(Base):
    __tablename__ = "guard_admins_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("guard_chats.id"))
    user_id: Mapped[int] = mapped_column(BigInteger)
    
    chat: Mapped["Chat"] = relationship(back_populates="admins")

# Update Chat relationship
Chat.admins = relationship("AdminCache", back_populates="chat", cascade="all, delete-orphan")

