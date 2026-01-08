from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, desc
from bot.core.database import get_session
from bot.core.models import Log

router = Router()

LOGS_PER_PAGE = 10

@router.callback_query(F.data.startswith("logs:"))
async def show_logs(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    chat_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0
    
    offset = page * LOGS_PER_PAGE
    
    async for session in get_session():
        # Fetch logs
        stmt = select(Log).where(Log.chat_id == chat_id).order_by(desc(Log.timestamp)).offset(offset).limit(LOGS_PER_PAGE)
        result = await session.execute(stmt)
        logs = result.scalars().all()
        
        # Check if there are more
        stmt_count = select(Log.id).where(Log.chat_id == chat_id).order_by(desc(Log.timestamp)).offset(offset + LOGS_PER_PAGE).limit(1)
        has_next = (await session.execute(stmt_count)).first() is not None

    if not logs:
        text = "📄 **Логи действий**\n\nЗаписей пока нет."
    else:
        text = f"📄 **Логи действий (Страница {page + 1})**\n\n"
        for log in logs:
            time_str = log.timestamp.strftime("%d.%m %H:%M")
            # details: "Violation: type"
            reason = log.details.replace("Violation: ", "") if log.details else "Unknown"
            
            icon = "🗑"
            if log.action == "mute": icon = "🔇"
            elif log.action == "ban": icon = "🚫"
            
            text += f"{icon} `{log.user_id}`: {reason} ({time_str})\n"

    # Keyboard
    builder = InlineKeyboardBuilder()
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"logs:{chat_id}:{page-1}"))
    if has_next:
        nav_buttons.append(types.InlineKeyboardButton(text="Вперед ➡️", callback_data=f"logs:{chat_id}:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
        
    builder.row(types.InlineKeyboardButton(text="🔄 Обновить", callback_data=f"logs:{chat_id}:{page}"))
    builder.row(types.InlineKeyboardButton(text="🔙 Назад в меню", callback_data=f"select_chat:{chat_id}"))
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
