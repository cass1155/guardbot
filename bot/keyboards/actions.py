from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

def get_action_keyboard(chat_id: int, filter_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🗑 Удалить сообщение", callback_data=f"set_action:{chat_id}:{filter_type}:delete")
    builder.button(text="🔇 Мут", callback_data=f"set_action:{chat_id}:{filter_type}:mute")
    builder.button(text="🚫 Бан", callback_data=f"set_action:{chat_id}:{filter_type}:ban")
    builder.button(text="🔙 Назад", callback_data=f"filter_edit:{chat_id}:{filter_type}")
    builder.adjust(1)
    return builder.as_markup()
