from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.admin import get_filters_keyboard, get_filter_settings_keyboard

router = Router()

class FilterStates(StatesGroup):
    waiting_for_pattern = State()
    waiting_for_smart_word = State()

@router.callback_query(F.data.startswith("filters:"))
async def show_filters(callback: types.CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "Выберите фильтр для настройки:",
        reply_markup=get_filters_keyboard(chat_id)
    )

@router.callback_query(F.data.startswith("filter_edit:"))
async def edit_filter(callback: types.CallbackQuery):
    _, chat_id, filter_type = callback.data.split(":")
    
    from bot.core.database import get_session
    from bot.core.models import Filter
    from sqlalchemy import select

    is_active = False
    current_action = "delete"
    
    async for session in get_session():
        # Check if there are ANY active filters for this type
        stmt = select(Filter).where(
            Filter.chat_id == int(chat_id), 
            Filter.filter_type == filter_type
        )
        result = await session.execute(stmt)
        filters = result.scalars().all()
        
        if filters:
            # Check if any is active
            if any(f.is_active for f in filters):
                is_active = True
            # Get action from the first one (assuming uniform action per type)
            current_action = filters[0].action
    
    await callback.message.edit_text(
        f"Настройка фильтра: {filter_type.upper()}",
        reply_markup=get_filter_settings_keyboard(chat_id, filter_type, is_active, current_action)
    )

# Placeholder for Add/Remove logic
@router.callback_query(F.data.startswith("filter_add:"))
async def add_filter_prompt(callback: types.CallbackQuery, state: FSMContext):
    _, chat_id, filter_type = callback.data.split(":")
    await callback.message.answer(f"Отправьте паттерн/слово для фильтра {filter_type}:")
    await state.set_state(FilterStates.waiting_for_pattern)
    await state.update_data(chat_id=chat_id, filter_type=filter_type)

@router.message(FilterStates.waiting_for_pattern)
async def save_filter(message: types.Message, state: FSMContext):
    data = await state.get_data()
    chat_id = data["chat_id"]
    filter_type = data["filter_type"]
    action_mode = data.get("action")

    from bot.core.database import get_session
    from bot.core.models import Filter
    from sqlalchemy import select

    if action_mode == "remove":
        # Handle removal by ID
        try:
            filter_id = int(message.text)
            async for session in get_session():
                filter_obj = await session.get(Filter, filter_id)
                if filter_obj and filter_obj.chat_id == int(chat_id):
                    await session.delete(filter_obj)
                    await session.commit()
                    await message.answer(f"✅ Фильтр {filter_id} удален.")
                else:
                    await message.answer("❌ Фильтр не найден.")
        except ValueError:
            await message.answer("❌ Введите числовой ID.")
        
        await state.clear()
        return

    # Handle Creation
    pattern = message.text
    
    # Auto-convert simple words to smart regex
    if filter_type == "regex":
        # Check if it looks like a manual regex (has special chars)
        special_chars = r"\[](){}^$|*+?"
        if not any(char in pattern for char in special_chars):
            from bot.services.regex_generator import generate_smart_regex
            original_pattern = pattern
            pattern = generate_smart_regex(pattern)
            await message.answer(f"🪄 Автоматически преобразовано в умный фильтр:\n`{pattern}`")

    async for session in get_session():
        new_filter = Filter(chat_id=int(chat_id), filter_type=filter_type, pattern=pattern, action="delete")
        session.add(new_filter)
        await session.commit()
    
    await message.answer(f"✅ Фильтр добавлен для {filter_type}: `{pattern}`")
    await state.clear()
    
    # Return to filters menu
    await message.answer(
        "Назад к фильтрам:",
        reply_markup=get_filters_keyboard(chat_id)
    )

@router.callback_query(F.data.startswith("filter_list:"))
async def list_filters(callback: types.CallbackQuery):
    _, chat_id, filter_type = callback.data.split(":")
    
    from bot.core.database import get_session
    from bot.core.models import Filter
    from sqlalchemy import select

    async for session in get_session():
        stmt = select(Filter).where(Filter.chat_id == int(chat_id), Filter.filter_type == filter_type)
        result = await session.execute(stmt)
        filters = result.scalars().all()
    
    if not filters:
        await callback.message.answer(f"Список пуст для {filter_type}.")
        return

    text = f"📋 Фильтры ({filter_type}):\n"
    for f in filters:
        status = "🟢" if f.is_active else "🔴"
        pat = f.pattern if f.pattern else "(Правило включено)"
        text += f"{f.id}. {status} `{pat}` -> {f.action}\n"
    
    await callback.message.answer(text)

@router.callback_query(F.data.startswith("filter_toggle:"))
async def toggle_filter_category(callback: types.CallbackQuery):
    _, chat_id, filter_type = callback.data.split(":")
    chat_id = int(chat_id)

    # Logic: Toggle a "Global" rule for this category OR toggle all existing rules?
    # For "Logic" filters (Links, Caps, etc.), we usually have one rule with pattern='*' or None.
    # Let's try to find an existing rule for this type. If exists, toggle it. If not, create it.
    
    from bot.core.database import get_session
    from bot.core.models import Filter
    from sqlalchemy import select

    async for session in get_session():
        stmt = select(Filter).where(Filter.chat_id == chat_id, Filter.filter_type == filter_type)
        result = await session.execute(stmt)
        filters = result.scalars().all()
        
        if filters:
            # Toggle all
            new_state = not filters[0].is_active
            current_action = filters[0].action
            for f in filters:
                f.is_active = new_state
            await session.commit()
            status = "Включено" if new_state else "Выключено"
        else:
            # Create default rule
            new_filter = Filter(chat_id=chat_id, filter_type=filter_type, pattern="*", is_active=True, action="delete")
            session.add(new_filter)
            await session.commit()
            status = "Включено"
            new_state = True
            current_action = "delete"

    await callback.message.edit_reply_markup(
        reply_markup=get_filter_settings_keyboard(chat_id, filter_type, new_state, current_action)
    )
    await callback.answer(f"Фильтр {filter_type}: {status}")

@router.callback_query(F.data.startswith("filter_rem:"))
async def remove_filter_prompt(callback: types.CallbackQuery, state: FSMContext):
    _, chat_id, filter_type = callback.data.split(":")
    await callback.message.answer(f"Введите ID фильтра для удаления (из списка 📋):")
    await state.set_state(FilterStates.waiting_for_pattern) # Reusing state for simplicity, or create new
    # Actually let's create a new state for ID
    await state.update_data(chat_id=chat_id, filter_type=filter_type, action="remove")

# Update save_filter to handle removal if action is set

@router.callback_query(F.data.startswith("filter_action:"))
async def select_filter_action(callback: types.CallbackQuery):
    _, chat_id, filter_type = callback.data.split(":")
    from bot.keyboards.actions import get_action_keyboard
    
    await callback.message.edit_text(
        f"Выберите наказание для {filter_type}:",
        reply_markup=get_action_keyboard(int(chat_id), filter_type)
    )

@router.callback_query(F.data.startswith("set_action:"))
async def set_filter_action(callback: types.CallbackQuery):
    _, chat_id, filter_type, action = callback.data.split(":")
    chat_id = int(chat_id)
    
    from bot.core.database import get_session
    from bot.core.models import Filter
    from sqlalchemy import select, update

    async for session in get_session():
        # Update ALL filters of this type for this chat
        stmt = update(Filter).where(
            Filter.chat_id == chat_id, 
            Filter.filter_type == filter_type
        ).values(action=action)
        await session.execute(stmt)
        
        # If no filter exists, create a default one with this action (disabled)
        # Check if exists first
        check_stmt = select(Filter).where(Filter.chat_id == chat_id, Filter.filter_type == filter_type)
        result = await session.execute(check_stmt)
        if not result.first():
            # Create inactive rule with this action
            session.add(Filter(chat_id=chat_id, filter_type=filter_type, pattern="*", is_active=False, action=action))
            
        await session.commit()

    await callback.answer(f"Действие обновлено: {action}")
    # Go back to settings
    from bot.keyboards.admin import get_filter_settings_keyboard
    
    # Check active state again for UI
    is_active = False
    current_action = action
    
    async for session in get_session():
        stmt = select(Filter).where(
            Filter.chat_id == chat_id, 
            Filter.filter_type == filter_type
        )
        result = await session.execute(stmt)
        filters = result.scalars().all()
        
        if any(f.is_active for f in filters):
            is_active = True

    # Fetch timer for repeats
    extra_text = None
    if filter_type == "repeats" and filters:
        # We store timer in pattern. Default is 60.
        # If pattern is "*" or empty, treat as 60.
        pat = filters[0].pattern
        if pat and pat.isdigit():
            extra_text = f"{pat}с"
        else:
            extra_text = "60с"

    await callback.message.edit_text(
        f"Настройка фильтра: {filter_type.upper()}",
        reply_markup=get_filter_settings_keyboard(chat_id, filter_type, is_active, current_action, extra_text)
    )

@router.callback_query(F.data.startswith("repeats_timer:"))
async def cycle_repeats_timer(callback: types.CallbackQuery):
    chat_id = int(callback.data.split(":")[1])
    
    from bot.core.database import get_session
    from bot.core.models import Filter
    from sqlalchemy import select, update
    
    options = [10, 30, 60, 300]
    
    async for session in get_session():
        # Get current value
        stmt = select(Filter).where(Filter.chat_id == chat_id, Filter.filter_type == "repeats")
        result = await session.execute(stmt)
        f = result.scalar_one_or_none()
        
        current_val = 60
        if f and f.pattern and f.pattern.isdigit():
            current_val = int(f.pattern)
            
        # Find next option
        try:
            idx = options.index(current_val)
            next_val = options[(idx + 1) % len(options)]
        except ValueError:
            next_val = 60
            
        # Update
        if f:
            f.pattern = str(next_val)
        else:
            # Create if not exists (inactive)
            session.add(Filter(chat_id=chat_id, filter_type="repeats", pattern=str(next_val), is_active=False))
            
        await session.commit()
        
        # Refresh UI
        # We need to call edit_filter logic again basically, or just re-render
        # Let's re-render
        is_active = f.is_active if f else False
        current_action = f.action if f else "delete"
        
        await callback.message.edit_reply_markup(
            reply_markup=get_filter_settings_keyboard(chat_id, "repeats", is_active, current_action, f"{next_val}с")
        )
        await callback.answer(f"Таймер установлен: {next_val}с")


