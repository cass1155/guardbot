from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, ChatMemberUpdated
from sqlalchemy import select
from bot.core.database import get_session
from bot.core.models import Chat, ChatSettings

class ChatManagementMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        chat = data.get("event_chat")
        
        if not chat or chat.type == "private":
            return await handler(event, data)

        # Register chat if not exists
        # We use a simple check. Optimization: Cache "known chats" in Redis to avoid DB hit every msg
        
        # For now, let's do a quick DB check or upsert. 
        # To be efficient, we might only do this on specific events or use a localized cache.
        # But "ChatManagementMiddleware" usually implies ensuring the chat is in DB.
        
        # Let's use the session from data (we need to inject it first or create it)
        # We'll create a session here or assume a DB middleware runs before. 
        # Let's create a session context here for safety.
        
        async for session in get_session():
            stmt = select(Chat).where(Chat.id == chat.id)
            result = await session.execute(stmt)
            db_chat = result.scalar_one_or_none()

            if not db_chat:
                db_chat = Chat(id=chat.id, title=chat.title)
                session.add(db_chat)
                
                # Create default settings
                settings = ChatSettings(chat_id=chat.id)
                session.add(settings)
                
                await session.commit()
            elif db_chat.title != chat.title:
                db_chat.title = chat.title
                await session.commit()
        
        return await handler(event, data)
