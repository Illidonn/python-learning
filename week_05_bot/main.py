import asyncio
import logging
import sys
import sqlite3
from contextlib import closing
from pathlib import Path

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import BOT_TOKEN


BASE_DIR = Path(__file__).resolve().parent
VISITS_DB = BASE_DIR / "visits.db"

dp = Dispatcher()

def init_db():
    with closing(sqlite3.connect(VISITS_DB)) as con:
        with con:
            con.execute("""CREATE TABLE IF NOT EXISTS visits (user_id INTEGER PRIMARY KEY, visit_count INTEGER);""")

def track_visit(user_id):
    with closing(sqlite3.connect(VISITS_DB)) as con:
        with con:
            cur = con.cursor()

            sql_query = """INSERT INTO visits (user_id, visit_count)
                           VALUES (?, 1) 
                           ON CONFLICT(user_id) DO UPDATE    SET visit_count = visit_count + 1 
                           RETURNING visit_count"""
            cur.execute(sql_query, (user_id,))
            num_visit = cur.fetchone()[0]
      
    return num_visit

@dp.message(F.text & ~F.text.startswith('/'))
async def text_echo_handler(message: Message) -> None:
    """
    Этот хендлер пока должен работать как эхо. Ловит текст, кроме начинающегося с '/'
    """
    await message.answer(message.text)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Этот хендлер получает сообщение от команды пользователя `/start`.
    Также ведёт счётчик посещений бота + сообщает номер посещения пользователю.
    """
    num_visit = track_visit(message.from_user.id)
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}! Номер твоего визита к данному боту - {num_visit}")

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """
    Этот хендлер получает сообщение от команды пользователя /help
    """
    await message.answer("Умею здороваться.\n"
                         "Также собираю статистику: количество уникальных пользователей и их визитов.\n"
                         "Напиши /start, чтобы я с тобой поздоровался. Также получишь информацию о количестве своих визитов (сколько раз ты написал /start)\n"
                         "Напиши /stats, чтобы увидеть счётчик своих визитов и количество уникальных пользователей бота.\n"
                         "Напиши /top, чтобы увидеть топ-5 id пользователей, писавших /start.\n"
                         "На обычный текст я реагирую как эхо.\n")

@dp.message(Command("stats"))
async def command_stats_handler(message: Message) -> None:
    """
    Этот хендлер получает сообщение от команды пользователя `/stats`.
    Показывает пользователю его личный счётчик визитов (сколько раз он жал /start) 
    и сколько всего уникальных пользователей у бота.
    """
    con = sqlite3.connect(VISITS_DB)
    cur = con.cursor()
    sql_query = "SELECT visit_count FROM visits WHERE user_id = ?"
    cur.execute(sql_query, (message.from_user.id, ))
    result = cur.fetchone()
    if result:
        num_visit = result[0]
    else:
        num_visit = 0
    cur.execute("SELECT COUNT(*) FROM visits")
    total_users = cur.fetchone()[0]
    con.close()
    
    await message.answer(f"Твой счётчик визитов: {num_visit}. Количество уникальных пользователей у бота - {total_users}")

@dp.message(Command("top"))
async def command_top_handler(message: Message) -> None:
    
    with closing(sqlite3.connect(VISITS_DB)) as con:
        cur = con.cursor()

        cur.execute(
        """SELECT user_id, visit_count 
        FROM visits 
        ORDER BY visit_count DESC 
        LIMIT 5;""")
        rows = cur.fetchall()

    if rows: 
        text = "\n".join([f"{rank}. {user_id}: {count}" for rank, (user_id, count) in enumerate(rows, start=1)])
    else:
        text = "Список пользователей пока пуст."
     
    await message.answer(text)

async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    init_db()
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())