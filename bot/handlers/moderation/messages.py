from aiogram import Router, F, types
from bot.services.moderation import moderate_message
from bot.core.loader import bot

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def check_message(message: types.Message, is_admin: bool = False):
    # Skip admins if configured (default behavior usually is to skip)
    # is_admin is injected by AuthMiddleware
    # Check settings for admin immunity
    if is_admin:
        from bot.core.database import get_session
        from bot.core.models import ChatSettings
        from sqlalchemy import select
        
        should_ignore = True
        async for session in get_session():
            stmt = select(ChatSettings).where(ChatSettings.chat_id == message.chat.id)
            result = await session.execute(stmt)
            settings = result.scalar_one_or_none()
            if settings:
                should_ignore = settings.ignore_admins
        
        if should_ignore:
            return

    await moderate_message(bot, message)
