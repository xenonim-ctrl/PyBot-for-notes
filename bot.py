import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, filters, F
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Импорты твоих модулей — ориентируйся как у тебя
from db import create_db_pool, add_record, get_records, get_record_by_id, delete_record, update_record_datetime, \
    get_result, add_result, get_our_result
from states import Form
from functions import main_keyboard, category_keyboard, format_record, CATEGORY_TABLE

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS").split(',')))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# ---------------------------
# In-memory user contexts:
# USER_CONTEXT[user_id] = [ {"table": "...", "id": 123, "title": "...", "created_at": datetime, "category": "...", "raw": {...}}, ... ]
# ---------------------------
USER_CONTEXT: dict[int, list[dict]] = {}


# ================== Проверка пользователя ==================
async def check_user(message: types.Message):
    if message.from_user.id not in ALLOWED_USERS:
        username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        await message.answer(f"Доступ запрещён ❌ {username}")
        return False
    return True


# ================== Старт ==================
@dp.message(filters.Command("start"))
async def start(message: types.Message):
    if not await check_user(message):
        return
    username = f"{message.from_user.first_name}" if message.from_user.first_name else message.from_user.username
    await message.answer(f"Приветик! {username}❤️ Что будем делать?", reply_markup=main_keyboard())


# ================== Главное меню: Записать ==================
@dp.message(lambda message: message.text == "Записать")
async def write_menu(message: types.Message, state: FSMContext):
    if not await check_user(message):
        return
    await state.set_state(Form.category)
    await message.answer("Выбери категорию для записи:", reply_markup=category_keyboard())


# ================== Главное меню: Прочитать ==================
@dp.message(lambda message: message.text == "Прочитать")
async def read_menu(message: types.Message):
    if not await check_user(message):
        return
    await show_records_menu(message)  # покажем агрегированный список (все таблицы)


# ================== Показ списка записей (агрегированный или по поиску) ==================
async def show_records_menu(call_or_message, search_query: str | None = None):
    """
    Если вызывается из Message — show as message.answer,
    если из CallbackQuery — edit message with inline keyboard.

    Формирует USER_CONTEXT[user_id] — список видимых записей (для навигации).
    Кнопки используют callback_data формата: ctx_{user_id}_{index}
    """
    user_id = call_or_message.from_user.id
    aggregated: list[dict] = []

    # Собираем все записи по всем таблицам
    for category, table in CATEGORY_TABLE.items():
        rows = await get_records(table, user_id)
        for row in rows:
            aggregated.append({
                "table": table,
                "id": row["id"],
                "title": row.get("title") or "",
                "created_at": row["created_at"],
                "raw": row,
                "category": category
            })

    # Применяем поиск, если есть
    if search_query:
        q = search_query.lower()
        filtered = []
        for item in aggregated:
            row = item["raw"]
            found = False
            for v in row.values():
                if isinstance(v, str) and q in v.lower():
                    found = True
                    break
            if found:
                filtered.append(item)
        aggregated = filtered

    # Сохраняем в контексте пользователя

    # сортируем по created_at перед сохранением !!!!!!!!!!
    aggregated.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    USER_CONTEXT[user_id] = aggregated


    if not aggregated:
        if isinstance(call_or_message, types.CallbackQuery):
            await call_or_message.message.edit_text("Нет записей для чтения.", reply_markup=None)
        else:
            await call_or_message.answer("Нет записей для чтения.", reply_markup=main_keyboard())
        return

    # Формируем инлайн-кнопки (по агрегированному списку)
    buttons: list[list[InlineKeyboardButton]] = []
    for idx, item in enumerate(aggregated):
        cat = item["category"]
        title = item["title"]
        date_str = item["created_at"].strftime("%d.%m.%Y")
        text = f"{cat} — {title} — {date_str}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"ctx_{user_id}_{idx}")])

    # Поиск (глобальный по всем записям) и Главное меню
    buttons.append([InlineKeyboardButton(text="🔍 Поиск", callback_data="search_all")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    if isinstance(call_or_message, types.CallbackQuery):
        await call_or_message.message.edit_text("Выберите запись:", reply_markup=kb)
    else:
        await call_or_message.answer("Выберите запись:", reply_markup=kb)


# ================== FSM: Выбор категории (запись) ==================
@dp.message(Form.category)
async def category_chosen(message: types.Message, state: FSMContext):
    category = message.text
    await state.update_data(category=category)

    if category == "Расклад":
        await state.set_state(Form.spread_title)
        await message.answer("Введите название расклада:")
    elif category == "Сон":
        await state.set_state(Form.dream_title)
        await message.answer("Введите название сна:")
    elif category == "Предчувствие":
        await state.set_state(Form.premonition_title)
        await message.answer("Введите название предчувствия:")
    elif category == "Ритуал":
        await state.set_state(Form.ritual_title)
        await message.answer("Введите название ритуала:")
    else:
        await message.answer("Выберите корректную категорию.", reply_markup=main_keyboard())
        await state.clear()


# ================== FSM: Расклады (пример) ==================
@dp.message(Form.spread_title)
async def spread_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Form.spread_question)
    await message.answer("Введите вопрос:")


@dp.message(Form.spread_question)
async def spread_question(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)
    await state.set_state(Form.spread_cards)
    await message.answer("Введите карты через + (например: Луна+Дурак+4 Жезлов):")


@dp.message(Form.spread_cards)
async def spread_cards(message: types.Message, state: FSMContext):
    await state.update_data(cards=message.text)
    await state.set_state(Form.spread_interpretation)
    await message.answer("Введите трактовку расклада:")


@dp.message(Form.spread_interpretation)
async def spread_interpretation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_record("spreads", message.from_user.id,
                     title=data["title"],
                     question=data["question"],
                     cards=data["cards"],
                     interpretation=message.text)
    username = message.from_user.first_name or message.from_user.username
    await message.answer(f"Расклад сохранён ✅, {username}", reply_markup=main_keyboard())
    await state.clear()

# ================== FSM: Сон ==================
@dp.message(Form.dream_title)
async def dream_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Form.dream_text)
    await message.answer("Введите текст сна:")

@dp.message(Form.dream_text)
async def dream_text(message: types.Message, state: FSMContext):
    await state.update_data(dream_text=message.text)
    await state.set_state(Form.dream_interpretation)
    await message.answer("Введите трактовку сна:")

@dp.message(Form.dream_interpretation)
async def dream_interpretation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_record("dreams", message.from_user.id,
                     title=data["title"],
                     dream_text=data["dream_text"],
                     interpretation=message.text)
    username = message.from_user.first_name or message.from_user.username
    await message.answer(f"Сон сохранён ✅, {username}", reply_markup=main_keyboard())
    await state.clear()


# ================== FSM: Предчувствие ==================
@dp.message(Form.premonition_title)
async def premonition_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Form.premonition_text)
    await message.answer("Введите текст предчувствия:")

@dp.message(Form.premonition_text)
async def premonition_text(message: types.Message, state: FSMContext):
    await state.update_data(premonition_text=message.text)
    await state.set_state(Form.premonition_interpretation)
    await message.answer("Введите трактовку предчувствия:")

@dp.message(Form.premonition_interpretation)
async def premonition_interpretation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_record("premonitions", message.from_user.id,
                     title=data["title"],
                     premonition_text=data["premonition_text"],
                     interpretation=message.text)
    username = message.from_user.first_name or message.from_user.username
    await message.answer(f"Предчувствие сохранено ✅, {username}", reply_markup=main_keyboard())
    await state.clear()


# ================== FSM: Ритуал ==================
@dp.message(Form.ritual_title)
async def ritual_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(Form.ritual_purpose)
    await message.answer("Введите цель ритуала:")

@dp.message(Form.ritual_purpose)
async def ritual_purpose(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    await state.set_state(Form.ritual_tools)
    await message.answer("Введите инструменты:")

@dp.message(Form.ritual_tools)
async def ritual_tools(message: types.Message, state: FSMContext):
    await state.update_data(tools=message.text)
    await state.set_state(Form.ritual_action)
    await message.answer("Введите действия ритуала:")

@dp.message(Form.ritual_action)
async def ritual_action(message: types.Message, state: FSMContext):
    await state.update_data(action=message.text)
    await state.set_state(Form.ritual_feelings)
    await message.answer("Введите ощущения после ритуала:")

@dp.message(Form.ritual_feelings)
async def ritual_feelings(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await add_record("rituals", message.from_user.id,
                     title=data["title"],
                     purpose=data["purpose"],
                     tools=data["tools"],
                     action=data["action"],
                     feelings=message.text)
    username = message.from_user.first_name or message.from_user.username
    await message.answer(f"Ритуал сохранён ✅, {username}", reply_markup=main_keyboard())
    await state.clear()

# ================== Просмотр записи из контекста ==================
@dp.callback_query(lambda c: c.data and (c.data.startswith("ctx_") or c.data.startswith("view_")))
async def read_record_ctx(call: types.CallbackQuery):
    """
    Обработка просмотра записи из контекста (ctx_{user_id}_{index})
    Навигация и операции опираются на USER_CONTEXT[user_id].
    """
    data = call.data
    parts = data.split("_")
    if len(parts) < 3:
        await call.answer("Неверные данные.")
        return
    try:
        _prefix, user_id_str, idx_str = parts[0], parts[1], parts[2]
        user_id = int(user_id_str)
        index = int(idx_str)
    except Exception:
        await call.answer("Неверные данные.")
        return

    # безопасность: только тот, кто запрашивал контекст, может им пользоваться
    if call.from_user.id != user_id:
        await call.answer("Этот список не принадлежит вам.", show_alert=True)
        return

    ctx_list = USER_CONTEXT.get(user_id, [])
    if not ctx_list or index < 0 or index >= len(ctx_list):
        await call.answer("Запись не найдена в текущем списке.")
        return

    item = ctx_list[index]
    table = item["table"]
    record_id = item["id"]

    # Получаем свежую запись из БД
    record = await get_record_by_id(table, record_id)
    if not record:
        await call.answer("Запись не найдена (удалена?).")
        # обновим контекст меню
        await show_records_menu(call)
        return

    text = format_record(record, table)

    # Кнопки: навигация по ctx list (стрелки), delete, move date, back to list
    buttons: list[list[InlineKeyboardButton]] = []
    nav_row: list[InlineKeyboardButton] = []
    if index > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Предыдущая",
            callback_data=f"ctx_{user_id}_{index-1}"
        ))
    if index < len(ctx_list) - 1:
        nav_row.append(InlineKeyboardButton(
            text="Следующая ▶️",
            callback_data=f"ctx_{user_id}_{index+1}"
        ))
    if nav_row:
        buttons.append(nav_row)

    # операции: delete и move (контекстные версии) + кнопка итога
    buttons.append([
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_ctx_{user_id}_{index}"),
        InlineKeyboardButton(text="📆 Перенести дату", callback_data=f"manual_move_ctx_{user_id}_{index}")
    ])
    # Итог
    result_text = await get_result(table, record_id)

    if result_text:
        buttons.append([
            InlineKeyboardButton(
                text="📄 Просмотреть итог",
                callback_data=f"shows_result_ctx_{user_id}_{index}"

            ),
            InlineKeyboardButton(
                text="✏️ Перезаписать итог",
                callback_data=f"result_add_ctx_{user_id}_{index}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="➕ Добавить итог",
                callback_data=f"result_add_ctx_{user_id}_{index}"
            )
        ])

    # Назад к списку (контекст)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data=f"back_to_list_ctx_{user_id}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)

# ПРОБУЕМ ИТОГИ
# Просмотр итога (robust parsing)
import re

# ================== Просмотр Итога ==================

@dp.callback_query(F.data.startswith("shows_result_ctx_"))
async def view_result_ctx(call: types.CallbackQuery):
    await call.answer()  # подтверждаем callback

    parts = call.data.split("_")  # ['show', 'result', 'ctx', user_id, index]
    try:
        user_id = int(parts[3])
        index = int(parts[4])
    except (IndexError, ValueError):
        await call.message.answer("Неверные данные hhh.")
        return

    if call.from_user.id != user_id:
        await call.message.answer("Это не ваш результат.")
        return

    ctx_list = USER_CONTEXT.get(user_id, [])
    if index >= len(ctx_list):
        await call.message.answer("Запись не найдена.")
        return

    entry = ctx_list[index]
    record_id = entry["id"]
    category = entry.get("category")  # если есть

    result = await get_our_result(user_id, record_id, category_name=category)
    if not result:
        await call.message.answer("Итог не найден.")
        return

    text = f"<b>Итог:</b>\n{result['result_text']}"
    await call.message.answer(text, parse_mode="HTML")


# Перезапись
@dp.callback_query(lambda c: c.data and c.data.startswith("result_add_ctx_"))
async def result_add_ctx(call: types.CallbackQuery, state: FSMContext):
    parts = call.data.split("_")
    user_id = int(parts[3])
    index = int(parts[4])

    if call.from_user.id != user_id:
        await call.answer("Нельзя менять чужой результат.", show_alert=True)
        return

    ctx_list = USER_CONTEXT.get(user_id, [])
    if not ctx_list or index >= len(ctx_list):
        await call.answer("Запись не найдена.", show_alert=True)
        return

    entry = ctx_list[index]
    table = entry["table"]
    record_id = entry["id"]
    category = entry["category"]  # добавляем категорию для add_result

    await state.update_data(result_ctx=(user_id, category, record_id))
    await state.set_state(Form.add_result)
    await call.message.answer("Введите текст итога:")


# Обработчик Итога
@dp.message(Form.add_result)
async def add_result_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if "result_ctx" not in data:
        await message.answer("Ошибка — запись не найдена.")
        await state.clear()
        return

    user_id, category, reference_id = data["result_ctx"]
    text = message.text.strip()
    if not text:
        await message.answer("Текст не может быть пустым. Попробуйте снова.")
        return

    await add_result(user_id, category, reference_id, text)

    await message.answer("Итог сохранен ✅")
    await state.clear()


# ================== Удаление (контекстная версия) ==================
@dp.callback_query(lambda c: c.data and c.data.startswith("delete_ctx_"))
async def delete_record_ctx_callback(call: types.CallbackQuery):
    # формат: delete_ctx_{user_id}_{index}
    parts = call.data.split("_")
    if len(parts) != 4:
        await call.answer("Неверные данные.")
        return
    _, _ctx, user_id_str, idx_str = parts
    user_id = int(user_id_str)
    index = int(idx_str)

    if call.from_user.id != user_id:
        await call.answer("Нельзя удалять чужие записи.", show_alert=True)
        return

    ctx = USER_CONTEXT.get(user_id, [])
    if index < 0 or index >= len(ctx):
        await call.answer("Элемент не найден.", show_alert=True)
        return

    entry = ctx[index]
    table = entry["table"]
    rec_id = entry["id"]

    # удаляем в БД
    await delete_record(table, rec_id)

    # удаляем из контекста
    ctx.pop(index)
    USER_CONTEXT[user_id] = ctx

    await call.answer("Запись удалена ✅", show_alert=True)
    # Обновляем список (контекст) — если есть элементы, показать их, иначе показать общий список
    if ctx:
        await show_records_menu(call)
    else:
        await show_records_menu(call)


# ================== Перенос даты (контекстная версия) ==================
@dp.callback_query(lambda c: c.data and c.data.startswith("manual_move_ctx_"))
async def manual_move_ctx_callback(call: types.CallbackQuery, state: FSMContext):
    # формат: manual_move_ctx_{user_id}_{index}
    parts = call.data.split("_")
    # manual, move, ctx, user_id, index → минимум 5 частей
    if len(parts) < 5:
        await call.answer("Неверные данные.")
        return

    user_id_str = parts[-2]
    idx_str = parts[-1]

    user_id = int(user_id_str)
    index = int(idx_str)

    if call.from_user.id != user_id:
        await call.answer("Нельзя менять дату чужой записи.", show_alert=True)
        return

    ctx = USER_CONTEXT.get(user_id, [])
    if index < 0 or index >= len(ctx):
        await call.answer("Элемент не найден.", show_alert=True)
        return

    entry = ctx[index]
    table = entry["table"]
    rec_id = entry["id"]

    await state.update_data(move_record_ctx=(user_id, index, table, rec_id))
    await state.set_state(Form.move_datetime)
    await call.message.answer("Введите дату в формате ДД.MM.ГГГГ ЧЧ:ММ")



# ================== Обработчик ввода даты ИЛИ ввода слова для поиска (используем одно состояние) ==================
@dp.message(Form.move_datetime)
async def manual_date_or_search_input(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # 1) глобальный поиск (если был установлен флаг search_global)
    if data.get("search_global"):
        query = message.text.strip()
        user_id = message.from_user.id
        aggregated: list[dict] = []
        for category, table in CATEGORY_TABLE.items():
            rows = await get_records(table, user_id)
            for row in rows:
                if any(isinstance(v, str) and query.lower() in v.lower() for v in row.values()):
                    aggregated.append({
                        "table": table,
                        "id": row["id"],
                        "title": row.get("title") or "",
                        "created_at": row["created_at"],
                        "raw": row,
                        "category": category
                    })
        aggregated.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        USER_CONTEXT[user_id] = aggregated
        await state.clear()

        if not aggregated:
            await message.answer("Ничего не найдено.")
            return

        # показать результаты поиска как набор ctx-кнопок
        buttons: list[list[InlineKeyboardButton]] = []
        for idx, item in enumerate(aggregated):
            cat = item["category"]
            title = item["title"]
            date_str = item["created_at"].strftime("%d.%m.%Y")
            buttons.append([InlineKeyboardButton(text=f"{cat} — {title} — {date_str}", callback_data=f"ctx_{user_id}_{idx}")])
        buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")])
        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(f"Найдено записей: {len(aggregated)}", reply_markup=kb)
        return

    # 2) перенос даты из контекста (move_record_ctx)
    if "move_record_ctx" in data:
        user_id, index, table, rec_id = data["move_record_ctx"]
        if message.from_user.id != user_id:
            await message.answer("Нельзя менять дату чужой записи.")
            await state.clear()
            return
        try:
            new_datetime = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer("Неверный формат даты. Попробуйте снова (ДД.MM.ГГГГ ЧЧ:ММ).")
            return

        await update_record_datetime(table, rec_id, new_datetime)
        await message.answer("Дата записи обновлена ✅")
        await state.clear()

        # пересобрать контекст и показать список (пользователь сможет открыть запись)
        await show_records_menu(message)
        return

    # 3) перенос даты в non-ctx режиме (если вдруг использовали другой путь) — ничего не ломаем:
    if "move_record" in data:
        table, rec_id = data["move_record"]
        try:
            new_datetime = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer("Неверный формат даты. Попробуйте снова (ДД.MM.ГГГГ ЧЧ:ММ).")
            return
        await update_record_datetime(table, rec_id, new_datetime)
        await message.answer("Дата записи обновлена ✅")
        await state.clear()
        await show_records_menu(message)
        return

    # Если ни одно условие не подошло — просто очищаем состояние
    await state.clear()
    await message.answer("Неизвестная операция — отменено.")


# ================== Назад к списку (контекст) ==================
@dp.callback_query(lambda c: c.data and c.data.startswith("back_to_list_ctx_"))
async def back_to_list_ctx(call: types.CallbackQuery):
    # формат: back_to_list_ctx_{user_id}
    parts = call.data.split("_")
    # back, to, list, ctx, user_id → минимум 5 частей
    if len(parts) < 5:
        await call.answer("Неверные данные.")
        return

    user_id_str = parts[-1]
    user_id = int(user_id_str)

    if call.from_user.id != user_id:
        await call.answer("Это не ваш список.", show_alert=True)
        return

    ctx = USER_CONTEXT.get(user_id, [])
    if not ctx:
        await show_records_menu(call)
        return

    buttons: list[list[InlineKeyboardButton]] = []
    for idx, item in enumerate(ctx):
        cat = item["category"]
        title = item["title"]
        date_str = item["created_at"].strftime("%d.%m.%Y")
        buttons.append([InlineKeyboardButton(
            text=f"{cat} — {title} — {date_str}",
            callback_data=f"ctx_{user_id}_{idx}"
        )])
    buttons.append([InlineKeyboardButton(text="🔍 Поиск", callback_data="search_all")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="back")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("Выберите запись:", reply_markup=kb)



# ================== Поиск: начало (глобальный) ==================
@dp.callback_query(lambda c: c.data and c.data == "search_all")
async def search_all_callback(call: types.CallbackQuery, state: FSMContext):
    # переход в состояние ввода поискового слова
    await state.update_data(search_global=True)
    await state.set_state(Form.move_datetime)  # используем существующее состояние для ввода строки
    await call.message.answer("Введите слово для поиска (будет искать во всех текстовых полях всех записей):")


# ================== Главное меню ==================
@dp.callback_query(lambda c: c.data == "back")
async def back_callback(call: types.CallbackQuery):
    await call.message.answer("Главное меню:", reply_markup=main_keyboard())
    # удаляем предыдущее сообщение с клавой
    try:
        await call.message.delete()
    except Exception:
        pass


# ================== Поддержка старого (table-style) просмотра ==================
@dp.callback_query(lambda c: c.data and c.data.startswith("read_"))
async def read_record_table_style(call: types.CallbackQuery):
    # формат: read_{table}_{record_id}_{idx} (table может содержать _)
    parts = call.data.split("_")[1:]
    if len(parts) < 2:
        await call.answer("Неверные данные.")
        return

    # Попробуем распарсить: предположим что последние два элемента — id и idx
    try:
        record_id = int(parts[-2])
        index = int(parts[-1])
        table = "_".join(parts[:-2])
    except Exception:
        # fallback: если нет idx — id последний
        try:
            record_id = int(parts[-1])
            index = 0
            table = "_".join(parts[:-1])
        except Exception:
            await call.answer("Неверные данные.")
            return

    # получаем список записей таблицы
    records = await get_records(table, call.from_user.id)
    index = next((i for i, r in enumerate(records) if r["id"] == record_id), 0)
    if index < 0 or index >= len(records):
        await call.answer("Запись не найдена.")
        return

    record = records[index]
    text = format_record(record, table)

    buttons = []
    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️ Предыдущая",
            callback_data=f"read_{table}_{records[index-1]['id']}_{index-1}"
        ))
    if index < len(records) - 1:
        nav_row.append(InlineKeyboardButton(
            text="Следующая ▶️",
            callback_data=f"read_{table}_{records[index+1]['id']}_{index+1}"
        ))
    if nav_row:
        buttons.append(nav_row)

    buttons.append([
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{table}_{record_id}_{index}"),
        InlineKeyboardButton(text="📆 Перенести дату", callback_data=f"manual_move_{table}_{record_id}_{index}")
    ])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back")])
    # Итог
    parts = call.data.split("_")
    user_id = int(parts[2])
    record_id = int(parts[3])
    result_text = await get_result(table, record_id)
    if result_text:
        buttons.append([
            InlineKeyboardButton(
                text="📄 Просмотреть итог",
                callback_data=f"shows_result_ctx_{user_id}_{index}"
            ),
            InlineKeyboardButton(
                text="✏️ Перезаписать итог",
                callback_data=f"result_add_ctx_{user_id}_{index}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text="➕ Добавить итог",
                callback_data=f"result_add_ctx_{user_id}_{index}"
            )
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)


# ================== Удаление (table-style, non-ctx) ==================
@dp.callback_query(lambda c: c.data and c.data.startswith("delete_"))
async def delete_record_callback(call: types.CallbackQuery):
    parts = call.data.split("_")[1:]
    # reconstruct table
    if len(parts) >= 3:
        table = "_".join(parts[:-2])
        record_id = int(parts[-2])
        index = int(parts[-1])
    elif len(parts) == 2:
        table = parts[0]
        record_id = int(parts[1])
        index = 0
    else:
        await call.answer("Неверные данные.")
        return

    await delete_record(table, record_id)
    await call.answer("Запись удалена ✅", show_alert=True)
    # После удаления — показать агрегированный список (как при Прочитать)
    await show_records_menu(call)


# ================== Перенос даты (non-ctx) ==================
@dp.callback_query(lambda c: c.data and c.data.startswith("manual_move_") and not c.data.startswith("manual_move_ctx_"))
async def manual_move_callback(call: types.CallbackQuery, state: FSMContext):
    # формат: manual_move_{table}_{record_id}_{index}
    parts = call.data.split("_")[1:]
    if len(parts) >= 3:
        table = "_".join(parts[:-2])
        record_id = int(parts[-2])
    elif len(parts) == 2:
        table = parts[0]
        record_id = int(parts[1])
    else:
        await call.answer("Неверные данные.")
        return

    await state.update_data(move_record=(table, record_id))
    await state.set_state(Form.move_datetime)
    await call.message.answer("Введите дату в формате ДД.MM.ГГГГ ЧЧ:ММ")



# ================== Запуск ==================
if __name__ == "__main__":
    async def main():
        await create_db_pool()
        await dp.start_polling(bot)

    asyncio.run(main())


