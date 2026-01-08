from aiogram import Router, F
from aiogram.types import ChatMemberUpdated
from aiogram.filters import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, ADMINISTRATOR, CREATOR, KICKED
from sqlalchemy import select, delete
from bot.core.database import get_session
from bot.core.models import AdminCache, Chat

router = Router()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> MEMBER))
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> ADMINISTRATOR))
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER >> ADMINISTRATOR))
async def on_bot_added_or_promoted(event: ChatMemberUpdated):
    # Bot added or promoted
    chat = event.chat
    print(f"DEBUG: Bot added/promoted in chat {chat.id} ({chat.title})")
    
    from bot.core.loader import bot
    
    async for session in get_session():
        # 1. Ensure Chat exists
        stmt = select(Chat).where(Chat.id == chat.id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            session.add(Chat(id=chat.id, title=chat.title))
            # Create default settings
            from bot.core.models import ChatSettings
            session.add(ChatSettings(chat_id=chat.id))
            await session.commit()
            
        # 2. If bot is admin, fetch all admins and cache them
        new_status = event.new_chat_member.status
        if new_status == "administrator":
            try:
                admins = await bot.get_chat_administrators(chat.id)
                for admin in admins:
                    if admin.user.is_bot:
                        continue
                        
                    # Check if exists
                    stmt_adm = select(AdminCache).where(AdminCache.chat_id == chat.id, AdminCache.user_id == admin.user.id)
                    res_adm = await session.execute(stmt_adm)
                    if not res_adm.scalar_one_or_none():
                        session.add(AdminCache(chat_id=chat.id, user_id=admin.user.id))
                
                await session.commit()
                print(f"DEBUG: Synced admins for chat {chat.id}")
            except Exception as e:
                print(f"Failed to sync admins for {chat.id}: {e}")

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER >> ADMINISTRATOR))
async def on_admin_promoted(event: ChatMemberUpdated):
    async for session in get_session():
        # Add to cache
        cache = AdminCache(chat_id=event.chat.id, user_id=event.new_chat_member.user.id)
        session.add(cache)
        await session.commit()

@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR >> MEMBER))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR >> IS_NOT_MEMBER))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR >> KICKED))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=CREATOR >> MEMBER))
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=CREATOR >> IS_NOT_MEMBER))
async def on_admin_demoted(event: ChatMemberUpdated):
    async for session in get_session():
        stmt = delete(AdminCache).where(
            AdminCache.chat_id == event.chat.id,
            AdminCache.user_id == event.new_chat_member.user.id
        )
        await session.execute(stmt)
        await session.commit()

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER >> IS_NOT_MEMBER))
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR >> IS_NOT_MEMBER))
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER >> KICKED))
@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=ADMINISTRATOR >> KICKED))
async def on_bot_removed(event: ChatMemberUpdated):
    # Bot removed from chat
    async for session in get_session():
        # Clear all admin cache for this chat
        stmt = delete(AdminCache).where(AdminCache.chat_id == event.chat.id)
        await session.execute(stmt)
        await session.commit()
