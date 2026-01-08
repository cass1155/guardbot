from aiogram import Router, F, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func, desc
from bot.core.database import get_session
from bot.core.models import Log

router = Router()

@router.callback_query(F.data.startswith("stats:"))
async def show_statistics(callback: types.CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    async for session in get_session():
        # 1. Total violations
        stmt_total = select(func.count(Log.id)).where(Log.chat_id == chat_id)
        total_violations = (await session.execute(stmt_total)).scalar() or 0
        
        # 2. Breakdown by Action
        stmt_actions = select(Log.action, func.count(Log.id)).where(Log.chat_id == chat_id).group_by(Log.action)
        actions_result = (await session.execute(stmt_actions)).all()
        
        # 3. Breakdown by Violation Type (parsing details)
        # Since details is "Violation: type", we can group by details or fetch all and process in python for small scale
        # For SQL efficiency, let's just group by details
        stmt_types = select(Log.details, func.count(Log.id)).where(Log.chat_id == chat_id).group_by(Log.details)
        types_result = (await session.execute(stmt_types)).all()
        
        # 4. Top Violators
        stmt_top = select(Log.user_id, func.count(Log.id)).where(Log.chat_id == chat_id).group_by(Log.user_id).order_by(desc(func.count(Log.id))).limit(5)
        top_users_result = (await session.execute(stmt_top)).all()

    # Format Output
    text = f"📊 **Статистика чата**\n\n"
    text += f"Всего нарушений: **{total_violations}**\n\n"
    
    text += "⚖️ **По наказаниям:**\n"
    if actions_result:
        for action, count in actions_result:
            text += f"- {action.capitalize()}: {count}\n"
    else:
        text += "Нет данных\n"
        
    text += "\n🛡 **По типам нарушений:**\n"
    if types_result:
        for details, count in types_result:
            # details format "Violation: type"
            v_type = details.replace("Violation: ", "").capitalize() if details else "Unknown"
            text += f"- {v_type}: {count}\n"
    else:
        text += "Нет данных\n"
        
    text += "\n🏆 **Топ нарушителей (ID):**\n"
    if top_users_result:
        for user_id, count in top_users_result:
            text += f"- `{user_id}`: {count} раз\n"
    else:
        text += "Нет данных\n"

    # Keyboard
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить", callback_data=f"stats:{chat_id}")
    builder.button(text="🔙 Назад", callback_data=f"select_chat:{chat_id}")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
