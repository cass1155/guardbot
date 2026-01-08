from aiogram import Router, F, types
from aiogram.filters import CommandStart
from sqlalchemy import select
from bot.core.database import get_session
from bot.core.models import AdminCache, Chat
from bot.keyboards.admin import get_chat_selection_keyboard, get_main_menu_keyboard

router = Router()

@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: types.Message):
    await show_chat_list(message, message.from_user.id)

@router.callback_query(F.data == "back_to_chats")
async def back_to_chats(callback: types.CallbackQuery):
    await show_chat_list(callback, callback.from_user.id)

@router.callback_query(F.data.startswith("chat_page:"))
async def change_chat_page(callback: types.CallbackQuery):
    page = int(callback.data.split(":")[1])
    await show_chat_list(callback, callback.from_user.id, page=page)

async def show_chat_list(event_obj, user_id: int, page: int = 0):
    from bot.core.loader import bot
    me = await bot.get_me()
    
    async for session in get_session():
        # Find chats where user is admin (distinct to avoid duplicates)
        stmt = select(Chat).join(AdminCache).where(AdminCache.user_id == user_id).distinct()
        result = await session.execute(stmt)
        chats = result.scalars().all()
        
        is_callback = isinstance(event_obj, types.CallbackQuery)
        message = event_obj.message if is_callback else event_obj
        
        if not chats:
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(text="➕ Добавить бота в группу", url=f"https://t.me/{me.username}?startgroup=true&admin=change_info+delete_messages+restrict_members+invite_users+pin_messages+manage_video_chats")
            builder.button(text="🔄 Обновить список", callback_data="back_to_chats")
            builder.button(text="ℹ️ О боте", callback_data="about_bot")
            builder.adjust(1)
            
            text = (
                "📉 **У вас пока нет активных чатов.**\n\n"
                "Чтобы добавить чат:\n"
                "1. Нажмите кнопку **Добавить бота в группу**.\n"
                "2. Выберите группу и подтвердите права.\n"
                "3. Нажмите **Обновить список**."
            )
            
            if is_callback:
                try:
                    if message.text and "У вас пока нет активных чатов" in message.text:
                        await event_obj.answer("❌ Новых чатов не найдено.", show_alert=True)
                        return
                    await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
                except Exception:
                    await event_obj.answer("❌ Новых чатов не найдено.", show_alert=True)
            else:
                await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")
            return

        # Pagination logic
        ITEMS_PER_PAGE = 5
        total_pages = (len(chats) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        
        # Ensure page is valid
        if page < 0: page = 0
        if page >= total_pages: page = total_pages - 1
        
        start_idx = page * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        current_chats = chats[start_idx:end_idx]

        # Chats exist
        if is_callback:
            try:
                await message.edit_text(
                    f"Выберите чат для управления (Стр. {page+1}/{total_pages}):",
                    reply_markup=get_chat_selection_keyboard(current_chats, me.username, page, total_pages)
                )
            except Exception as e:
                # Ignore "message is not modified" error
                if "message is not modified" in str(e):
                    await event_obj.answer("✅ Список актуален.")
                else:
                    raise e
        else:
            await message.answer(
                f"Выберите чат для управления (Стр. {page+1}/{total_pages}):",
                reply_markup=get_chat_selection_keyboard(current_chats, me.username, page, total_pages)
            )

@router.callback_query(F.data == "about_bot")
async def about_bot(callback: types.CallbackQuery):
    text = (
        "🤖 **GuardBot**\n\n"
        "Мощный бот для автоматической модерации и защиты ваших чатов.\n\n"
        "**🛡 Доступные фильтры:**\n"
        "• **Мат** — удаляет нецензурную лексику (можно настроить словарь).\n"
        "• **Ссылки** — запрещает отправку ссылок.\n"
        "• **Контакты** — блокирует номера телефонов и контактные карточки.\n"
        "• **Крипто** — ловит адреса криптокошельков (BTC, ETH, TRX).\n"
        "• **Каналы** — запрещает писать от имени каналов.\n"
        "• **Медиа** — запрещает фото, видео, файлы.\n"
        "• **CAPS** — удаляет сообщения, написанные капсом.\n"
        "• **Повторы** — удаляет дублирующиеся сообщения (флуд).\n"
        "• **Regex** — умные фильтры по шаблонам.\n\n"
        "**⚙️ Возможности:**\n"
        "• **Строгий режим** — включает все защиты сразу.\n"
        "• **Наказания** — удаление, мут или бан.\n"
        "• **Игнор админов** — бот не трогает администраторов.\n"
        "• **Статистика и Логи** — полная история нарушений.\n\n"
        "Разработано для безопасности ваших сообществ."
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_chats")
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data.startswith("select_chat:"))
async def select_chat_menu(callback: types.CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    # AuthMiddleware has already verified rights if we configured it correctly, 
    # but for safety/UI flow we just show the menu.
    
    await callback.message.edit_text(
        f"Управление чатом ID: {chat_id}\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(chat_id)
    )
