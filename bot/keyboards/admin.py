from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_chat_selection_keyboard(chats: list, bot_username: str, page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Chats
    for chat in chats:
        builder.button(text=chat.title, callback_data=f"select_chat:{chat.id}")
    builder.adjust(1)

    # Pagination
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"chat_page:{page-1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"chat_page:{page+1}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Add Bot to Group URL
    builder.row(InlineKeyboardButton(text="➕ Добавить бота в группу", url=f"https://t.me/{bot_username}?startgroup=true&admin=change_info+delete_messages+restrict_members+invite_users+pin_messages+manage_video_chats"))
    builder.row(InlineKeyboardButton(text="🔄 Обновить список", callback_data="back_to_chats"))
    
    return builder.as_markup()

def get_main_menu_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛡 Фильтры", callback_data=f"filters:{chat_id}")
    builder.button(text="⚙️ Настройки", callback_data=f"settings:{chat_id}")
    builder.button(text="📊 Статистика", callback_data=f"stats:{chat_id}")
    builder.button(text="📄 Логи", callback_data=f"logs:{chat_id}")
    builder.button(text="ℹ️ О боте", callback_data="about_bot")
    builder.button(text="🔙 Назад к чатам", callback_data="back_to_chats")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()

def get_filters_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    filters = [
        ("Keywords", "Ключевые слова"), 
        ("Regex", "Regex"), 
        ("Links", "Ссылки"), 
        ("Contacts", "Контакты"), 
        ("Crypto", "Крипто"), 
        ("Channels", "Каналы"),
        ("Mat", "Мат"), 
        ("Repeats", "Повторы"), 
        ("CAPS", "CAPS"), 
        ("Media", "Медиа")
    ]
    for f_code, f_name in filters:
        builder.button(text=f"🔹 {f_name}", callback_data=f"filter_edit:{chat_id}:{f_code.lower()}")
    builder.button(text="🔙 Назад", callback_data=f"select_chat:{chat_id}")
    builder.adjust(2)
    return builder.as_markup()

def get_filter_settings_keyboard(chat_id: int, filter_type: str, is_active: bool, current_action: str = "delete", extra_text: str = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    status_icon = "🟢" if is_active else "🔴"
    
    # Map action to Russian text
    action_map = {
        "delete": "Удаление",
        "mute": "Мут",
        "ban": "Бан"
    }
    action_text = action_map.get(current_action, "Удаление")
    
    # Logic-based filters don't need pattern management
    logic_filters = ["caps", "contacts", "repeats", "media", "crypto", "links", "channels"]
    
    if filter_type in logic_filters:
        builder.button(text=f"Вкл/Выкл {status_icon}", callback_data=f"filter_toggle:{chat_id}:{filter_type}")
        builder.button(text=f"⚖️ Действие ({action_text})", callback_data=f"filter_action:{chat_id}:{filter_type}")
        
        if filter_type == "repeats":
            timer_label = extra_text if extra_text else "60с"
            builder.button(text=f"⏱ Таймер ({timer_label})", callback_data=f"repeats_timer:{chat_id}")

        builder.button(text="🔙 Назад", callback_data=f"filters:{chat_id}")
        builder.adjust(1)
    else:
        builder.button(text="➕ Добавить", callback_data=f"filter_add:{chat_id}:{filter_type}")
        builder.button(text="➖ Удалить", callback_data=f"filter_rem:{chat_id}:{filter_type}")
        builder.button(text="📋 Список", callback_data=f"filter_list:{chat_id}:{filter_type}")
        builder.button(text=f"Вкл/Выкл {status_icon}", callback_data=f"filter_toggle:{chat_id}:{filter_type}")
        builder.button(text=f"⚖️ Действие ({action_text})", callback_data=f"filter_action:{chat_id}:{filter_type}")
        builder.button(text="🔙 Назад", callback_data=f"filters:{chat_id}")
        builder.adjust(2, 2, 1)
        
    return builder.as_markup()
