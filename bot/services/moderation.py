from sqlalchemy import select
from bot.core.database import get_session
from bot.core.models import Filter, Log
from bot.services.filters import check_regex, check_link, check_caps, check_keywords
from bot.services.punishment import delete_message, mute_user, ban_user
from aiogram import Bot
from aiogram.types import Message

async def moderate_message(bot: Bot, message: Message):
    # if not message.text and not message.caption:
    #    return

    text = message.text or message.caption or ""
    chat_id = message.chat.id
    user_id = message.from_user.id

    async for session in get_session():
        # Fetch active filters for this chat
        stmt = select(Filter).where(Filter.chat_id == chat_id, Filter.is_active == True)
        result = await session.execute(stmt)
        filters = result.scalars().all()

        violation = None
        action = "delete"

        for f in filters:
            is_violation = False
            if f.filter_type == "regex" and f.pattern:
                is_violation = check_regex(text, f.pattern)
            elif f.filter_type == "link":
                is_violation = check_link(text)
            elif f.filter_type == "caps":
                is_violation = check_caps(text)
            elif f.filter_type == "keywords" and f.pattern:
                is_violation = check_keywords(text, f.pattern.split(","))
            elif f.filter_type == "mat" and f.pattern:
                is_violation = check_keywords(text, f.pattern.split(","))
            elif f.filter_type == "crypto":
                from bot.services.filters import check_crypto
                is_violation = check_crypto(text)
            elif f.filter_type == "contacts":
                from bot.services.filters import check_phone
                if message.contact:
                    is_violation = True
                else:
                    is_violation = check_phone(text)
            elif f.filter_type == "media":
                from bot.services.filters import check_media
                is_violation = check_media(message)
            elif f.filter_type == "channels":
                # Check if message is sent on behalf of a channel
                if message.sender_chat:
                    # Allow if it's the chat itself (official posts)
                    if message.sender_chat.id != chat_id:
                        # Allow if it's an automatic forward (linked channel)
                        if not message.is_automatic_forward:
                            is_violation = True
            elif f.filter_type == "repeats":
                # Check for duplicate messages
                from bot.core.redis import redis_client
                import hashlib
                
                # Create a hash of the content
                content = text
                if message.photo: content += f"photo:{message.photo[-1].file_unique_id}"
                if message.video: content += f"video:{message.video.file_unique_id}"
                if message.document: content += f"doc:{message.document.file_unique_id}"
                
                msg_hash = hashlib.md5(content.encode()).hexdigest()
                key = f"last_msg:{chat_id}:{user_id}"
                
                last_hash = await redis_client.get(key)
                if last_hash == msg_hash:
                    is_violation = True
                
                # Get timer from pattern (default 60)
                try:
                    timer = int(f.pattern)
                except (ValueError, TypeError):
                    timer = 60

                # Save current hash
                await redis_client.set(key, msg_hash, ex=timer)

            if is_violation:
                violation = f.filter_type
                action = f.action
                break
        
        if violation:
            # Execute punishment
            if action == "delete":
                await delete_message(bot, chat_id, message.message_id)
            elif action == "mute":
                await delete_message(bot, chat_id, message.message_id)
                await mute_user(bot, chat_id, user_id)
            elif action == "ban":
                await delete_message(bot, chat_id, message.message_id)
                await ban_user(bot, chat_id, user_id)

            # Log violation
            log = Log(chat_id=chat_id, user_id=user_id, action=action, details=f"Violation: {violation}")
            session.add(log)
            await session.commit()
