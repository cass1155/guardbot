from aiogram import Bot
from aiogram.types import ChatPermissions
from datetime import timedelta, datetime

async def delete_message(bot: Bot, chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id, message_id)
    except Exception:
        pass

async def mute_user(bot: Bot, chat_id: int, user_id: int, duration_minutes: int = 60):
    until_date = datetime.now() + timedelta(minutes=duration_minutes)
    permissions = ChatPermissions(can_send_messages=False)
    try:
        await bot.restrict_chat_member(chat_id, user_id, permissions, until_date=until_date)
    except Exception:
        pass

async def ban_user(bot: Bot, chat_id: int, user_id: int):
    try:
        await bot.ban_chat_member(chat_id, user_id)
    except Exception as e:
        print(f"Failed to ban user {user_id} in {chat_id}: {e}")
