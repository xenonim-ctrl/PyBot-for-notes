from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

CATEGORY_TABLE = {
    "Расклад": "spreads",
    "Сон": "dreams",
    "Предчувствие": "premonitions",
    "Ритуал": "rituals"
}

def main_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Записать"), KeyboardButton(text="Прочитать")]],
        resize_keyboard=True
    )
    return kb

def category_keyboard(back=True):
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    rows = [
        [KeyboardButton(text="Расклад")],
        [KeyboardButton(text="Сон")],
        [KeyboardButton(text="Предчувствие")],
        [KeyboardButton(text="Ритуал")],
    ]
    if back:
        rows.append([KeyboardButton(text="Назад")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def build_record_kb(table, records, index):
    """Клавиатура для просмотра одной записи"""
    buttons = []

    # Навигация
    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton("◀️ Предыдущая", callback_data=f"read_{table}_{records[index-1]['id']}"))
    if index < len(records) - 1:
        nav_row.append(InlineKeyboardButton("Следующая ▶️", callback_data=f"read_{table}_{records[index+1]['id']}"))
    if nav_row:
        buttons.append(nav_row)

    # Действия с записью
    buttons.append([
        InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{table}_{records[index]['id']}"),
        InlineKeyboardButton("📆 Перенести дату", callback_data=f"move_{table}_{records[index]['id']}")
    ])

    # Главное меню
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_search_results_kb(records):
    """Клавиатура для результатов поиска"""
    buttons = []
    for rec in records:
        buttons.append([InlineKeyboardButton(
            text=f"{rec.get('title','Без названия')} — {rec['created_at'].strftime('%d.%m.%Y')}",
            callback_data=f"read_{rec['table']}_{rec['id']}"
        )])
    buttons.append([InlineKeyboardButton("🏠 Главное меню", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def format_record(record, category, result=None):
    text = f"📌 <b>{record.get('title','Без названия')}</b>\n"
    text += f"🗓 Дата: {record['created_at'].strftime('%d.%m.%Y %H:%M')}\n"

    if category == "spreads":
        text += f"❓ Вопрос: {record.get('question')}\n"
        text += f"🃏 Карты: {record.get('cards')}\n"
        text += f"📝 Трактовка: {record.get('interpretation')}\n"
    elif category == "dreams":
        text += f"💤 Сон: {record.get('dream_text')}\n"
        text += f"📝 Трактовка: {record.get('interpretation')}\n"
    elif category == "premonitions":
        text += f"🔮 Предчувствие: {record.get('premonition_text')}\n"
        text += f"📝 Трактовка: {record.get('interpretation')}\n"
    elif category == "rituals":
        text += f"🎯 Цель: {record.get('purpose')}\n"
        text += f"🛠 Инструменты: {record.get('tools')}\n"
        text += f"⚡ Действия: {record.get('action')}\n"
        text += f"💫 Ощущения: {record.get('feelings')}\n"

    if result:
        text += f"\n🎯 Итог: {result.get('result_text')}"

    return text

