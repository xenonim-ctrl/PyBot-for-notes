import os
import asyncpg
from dotenv import load_dotenv
from datetime import datetime
from functions import CATEGORY_TABLE

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = int(os.getenv("DB_PORT"))

# Глобальный пул
db_pool: asyncpg.Pool | None = None

# ================== Создание пула ==================
async def create_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            min_size=1,
            max_size=20,
            max_inactive_connection_lifetime=300
        )

# ================== Универсальные функции ==================
async def execute(query, *args):
    async with db_pool.acquire() as conn:
        try:
            return await conn.execute(query, *args)
        except (asyncpg.exceptions.ConnectionDoesNotExistError,
                asyncpg.exceptions.PostgresConnectionError):
            async with db_pool.acquire() as conn_retry:
                return await conn_retry.execute(query, *args)

async def fetch(query, *args):
    async with db_pool.acquire() as conn:
        try:
            return await conn.fetch(query, *args)
        except (asyncpg.exceptions.ConnectionDoesNotExistError,
                asyncpg.exceptions.PostgresConnectionError):
            async with db_pool.acquire() as conn_retry:
                return await conn_retry.fetch(query, *args)

async def fetchrow(query, *args):
    async with db_pool.acquire() as conn:
        try:
            row = await conn.fetchrow(query, *args)
        except (asyncpg.exceptions.ConnectionDoesNotExistError,
                asyncpg.exceptions.PostgresConnectionError):
            async with db_pool.acquire() as conn_retry:
                row = await conn_retry.fetchrow(query, *args)
        return dict(row) if row else None

# ================== Добавление записей ==================
async def add_record(table, user_id, **kwargs):
    now = datetime.now()
    if table == "spreads":
        await execute(
            "INSERT INTO spreads(user_id, created_at, title, question, cards, interpretation) "
            "VALUES($1,$2,$3,$4,$5,$6)",
            user_id, now, kwargs.get("title"), kwargs.get("question"),
            kwargs.get("cards"), kwargs.get("interpretation")
        )
    elif table == "dreams":
        await execute(
            "INSERT INTO dreams(user_id, created_at, title, dream_text, interpretation) "
            "VALUES($1,$2,$3,$4,$5)",
            user_id, now, kwargs.get("title"), kwargs.get("dream_text"),
            kwargs.get("interpretation")
        )
    elif table == "premonitions":
        await execute(
            "INSERT INTO premonitions(user_id, created_at, title, premonition_text, interpretation) "
            "VALUES($1,$2,$3,$4,$5)",
            user_id, now, kwargs.get("title"), kwargs.get("premonition_text"),
            kwargs.get("interpretation")
        )
    elif table == "rituals":
        await execute(
            "INSERT INTO rituals(user_id, created_at, title, purpose, tools, action, feelings) "
            "VALUES($1,$2,$3,$4,$5,$6,$7)",
            user_id, now, kwargs.get("title"), kwargs.get("purpose"),
            kwargs.get("tools"), kwargs.get("action"), kwargs.get("feelings")
        )
    elif table == "results":
        await execute(
            "INSERT INTO results(user_id, category, reference_id, result_text, created_at) "
            "VALUES($1,$2,$3,$4,$5)",
            user_id, kwargs.get("category"), kwargs.get("reference_id"),
            kwargs.get("result_text"), now
        )

# ================== Получение всех записей пользователя ==================
async def get_records(table, user_id):
    rows = await fetch(f"SELECT * FROM {table} WHERE user_id=$1 ORDER BY created_at DESC", user_id)
    return [dict(row) for row in rows]

# ================== Получение записи по ID ==================
async def get_record_by_id(table, record_id):
    return await fetchrow(f"SELECT * FROM {table} WHERE id=$1", record_id)

# ================== Поиск по слову ==================
async def search_records(table, user_id, keyword):
    keyword = f"%{keyword.lower()}%"
    query = f"""
        SELECT * FROM {table}
        WHERE user_id=$1 AND LOWER(title || ' ' || COALESCE(question,'') || ' ' || 
                                  COALESCE(cards,'') || ' ' || COALESCE(interpretation,'') ||
                                  COALESCE(dream_text,'') || COALESCE(premonition_text,'') ||
                                  COALESCE(purpose,'') || COALESCE(tools,'') || COALESCE(action,'') || COALESCE(feelings,'')) 
              LIKE $2
        ORDER BY created_at DESC
    """
    rows = await fetch(query, user_id, keyword)
    return [dict(row) for row in rows]

# ================== Обновление даты записи ==================
async def update_record_datetime(table, record_id, new_datetime: datetime):
    await execute(f"UPDATE {table} SET created_at=$1 WHERE id=$2", new_datetime, record_id)

# ================== Удаление записи ==================
async def delete_record(table, record_id):
    await execute(f"DELETE FROM {table} WHERE id=$1", record_id)

# ================== Результаты
async def get_result(category, reference_id):
    row = await fetchrow(
        "SELECT * FROM results WHERE category=$1 AND reference_id=$2 ORDER BY created_at DESC LIMIT 1",
        category, reference_id
    )
    return row

# ================== Обновление флага
async def add_result(user_id, category, reference_id, result_text):
    now = datetime.now()
    # переводим категорию в английское имя для БД
    category_db = CATEGORY_TABLE[category]  # 'Предчувствие' → 'premonitions', и т.д.

    await execute(
        "INSERT INTO results(user_id, category, reference_id, result_text, created_at) "
        "VALUES($1,$2,$3,$4,$5)",
        user_id, category_db, reference_id, result_text, now
    )

    # Обновляем флаг в основной таблице
    await execute(f"UPDATE {category_db} SET has_result=TRUE WHERE id=$1", reference_id)

# ================== Получение конкретного итога для записи
async def get_our_result(user_id: int, record_id: int, category_name: str = None):

    if category_name:
        category_db = CATEGORY_TABLE.get(category_name, category_name)
        query = """
            SELECT * FROM results
            WHERE user_id=$1 AND category=$2 AND reference_id=$3
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await fetchrow(query, user_id, category_db, record_id)
    else:
        query = """
            SELECT * FROM results
            WHERE user_id=$1 AND reference_id=$2
            ORDER BY created_at DESC
            LIMIT 1
        """
        row = await fetchrow(query, user_id, record_id)


    return row


