from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    # Выбор категории
    category = State()

    # Расклады
    spread_title = State()
    spread_question = State()
    spread_cards = State()
    spread_interpretation = State()

    # Сны
    dream_title = State()
    dream_text = State()
    dream_interpretation = State()

    # Предчувствия
    premonition_title = State()
    premonition_text = State()
    premonition_interpretation = State()

    # Ритуалы
    ritual_title = State()
    ritual_purpose = State()
    ritual_tools = State()
    ritual_action = State()
    ritual_feelings = State()

    # Итоги
    result_category = State()
    result_choose = State()
    add_result = State()

    # ================== Перенос даты ==================
    move_datetime = State()  # Для ввода новой даты при переносе записи

    # ================== Поиск ==================
    search_word = State()  # Для ввода слова при поиске
