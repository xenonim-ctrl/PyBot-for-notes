from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="Записать", callback_data="write"),
        InlineKeyboardButton(text="Прочитать", callback_data="read")
    )
    return kb

def category_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(text="Расклад", callback_data="category_spread"),
        InlineKeyboardButton(text="Сон", callback_data="category_dream"),
        InlineKeyboardButton(text="Предчувствие", callback_data="category_premonition"),
        InlineKeyboardButton(text="Ритуал", callback_data="category_ritual")
    )
    return kb
