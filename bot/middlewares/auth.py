from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.enums import ChatMemberStatus
from sqlalchemy import select
from bot.core.loader import bot
from bot.core.redis import redis_client
from bot.core.database import get_session
from bot.core.models import AdminCache

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        # If it's a callback from the admin panel, it usually contains chat_id in data
        # We need a convention. E.g. "action:chat_id:..."
        # Or we check if the event is in a chat (not private)
        
        chat = data.get("event_chat")
        
        # 1. Interaction within a group chat
        if chat and chat.type in ["group", "supergroup"]:
            # Check if user is admin
            is_admin = await self.check_admin(chat.id, user.id)
            if not is_admin:
                # If user is not admin, we might ignore or reply
                # For inline buttons in chat, we should ignore non-admins
                if isinstance(event, CallbackQuery):
                    await event.answer("Вы не администратор.", show_alert=True)
                    return
                # For messages, we just pass through (moderation logic handles it)
                # But we might want to flag "is_admin" in data
            else:
                # Sync to DB if admin
                await self.sync_admin_to_db(chat.id, user.id)
            
            data["is_admin"] = is_admin

        # 2. Interaction in Private Chat (Admin Panel)
        # If the callback data targets a specific chat, we must verify rights
        if isinstance(event, CallbackQuery) and event.data:
            parts = event.data.split(":")
            if len(parts) > 1 and parts[1].lstrip("-").isdigit():
                target_chat_id = int(parts[1])
                # Verify admin rights for this target chat
                is_admin = await self.check_admin(target_chat_id, user.id)
                if not is_admin:
                    await event.answer("Вы больше не администратор в этом чате.", show_alert=True)
                    return
                data["target_chat_id"] = target_chat_id

        return await handler(event, data)

    async def check_admin(self, chat_id: int, user_id: int) -> bool:
        cache_key = f"admin:{chat_id}:{user_id}"
        cached = await redis_client.get(cache_key)
        
        if cached is not None:
            return cached == "1"

        try:
            member = await bot.get_chat_member(chat_id, user_id)
            is_admin = member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
            
            # Cache for 5 minutes (short cache as per requirements to be strict)
            await redis_client.setex(cache_key, 300, "1" if is_admin else "0")
            return is_admin
        except Exception:
            return False

    async def sync_admin_to_db(self, chat_id: int, user_id: int):
        # Optimization: Check a separate redis key to avoid DB spam
        sync_key = f"db_synced:{chat_id}:{user_id}"
        if await redis_client.get(sync_key):
            return

        async for session in get_session():
            stmt = select(AdminCache).where(AdminCache.chat_id == chat_id, AdminCache.user_id == user_id)
            result = await session.execute(stmt)
            if not result.scalar_one_or_none():
                session.add(AdminCache(chat_id=chat_id, user_id=user_id))
                await session.commit()
        
        # Mark as synced for 1 hour
        await redis_client.setex(sync_key, 3600, "1")
