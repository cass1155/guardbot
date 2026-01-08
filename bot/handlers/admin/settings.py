from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from bot.core.database import get_session
from bot.core.models import ChatSettings

router = Router()

def get_settings_keyboard(chat_id: int, settings: ChatSettings) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    strict_icon = "🟢" if settings.strict_mode else "🔴"
    ignore_admins_icon = "🟢" if settings.ignore_admins else "🔴"
    
    builder.button(text=f"Строгий режим {strict_icon}", callback_data=f"set_toggle:{chat_id}:strict_mode")
    builder.button(text=f"Игнор админов {ignore_admins_icon}", callback_data=f"set_toggle:{chat_id}:ignore_admins")
    builder.button(text="🔙 Назад", callback_data=f"select_chat:{chat_id}")
    builder.adjust(1)
    return builder.as_markup()

@router.callback_query(F.data.startswith("settings:"))
async def show_settings(callback: types.CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    async for session in get_session():
        stmt = select(ChatSettings).where(ChatSettings.chat_id == chat_id)
        result = await session.execute(stmt)
        settings = result.scalar_one_or_none()
        
        if not settings:
            # Create if missing (should be created by middleware, but safety check)
            settings = ChatSettings(chat_id=chat_id)
            session.add(settings)
            await session.commit()

        await callback.message.edit_text(
            "⚙️ Настройки чата:",
            reply_markup=get_settings_keyboard(chat_id, settings)
        )

@router.callback_query(F.data.startswith("set_toggle:"))
async def toggle_setting(callback: types.CallbackQuery):
    _, chat_id, setting_name = callback.data.split(":")
    chat_id = int(chat_id)
    
    async for session in get_session():
        stmt = select(ChatSettings).where(ChatSettings.chat_id == chat_id)
        result = await session.execute(stmt)
        settings = result.scalar_one_or_none()
        
        if settings:
            current_val = getattr(settings, setting_name)
            new_val = not current_val
            setattr(settings, setting_name, new_val)
            
            # Strict Mode Logic: Enable all filters if turned ON
            if setting_name == "strict_mode" and new_val is True:
                from bot.core.models import Filter
                
                filter_types = [
                    "caps", "contacts", "repeats", "media", "crypto", 
                    "links", "channels", "mat", "keywords", "regex"
                ]
                
                for f_type in filter_types:
                    # Check if filter exists
                    stmt_f = select(Filter).where(Filter.chat_id == chat_id, Filter.filter_type == f_type)
                    result_f = await session.execute(stmt_f)
                    f = result_f.scalar_one_or_none()
                    
                    if f:
                        f.is_active = True
                    else:
                        # Create active filter
                        # For logic filters, pattern is not needed or default
                        # For regex/keywords, we create empty active filter (user can configure later)
                        session.add(Filter(chat_id=chat_id, filter_type=f_type, is_active=True))
            
            await session.commit()
            
            await callback.message.edit_reply_markup(
                reply_markup=get_settings_keyboard(chat_id, settings)
            )
