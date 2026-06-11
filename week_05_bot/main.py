import asyncio
import aiohttp
import logging
import sys
import sqlite3
from contextlib import closing
from pathlib import Path
import time

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message

from config import BOT_TOKEN


BASE_DIR = Path(__file__).resolve().parent
VISITS_DB = BASE_DIR / "visits.db"
RATE_CACHE = BASE_DIR / "rate_cache.db"
CACHE_TTL = 3600

dp = Dispatcher()

def init_db():
    with closing(sqlite3.connect(VISITS_DB)) as con:
        with con:
            con.execute("""CREATE TABLE IF NOT EXISTS visits (user_id INTEGER PRIMARY KEY, visit_count INTEGER);""")
    with closing(sqlite3.connect(RATE_CACHE)) as con:
        with con:
            con.execute("""CREATE TABLE IF NOT EXISTS rate_cache (currency TEXT PRIMARY KEY, rate REAL, fetched_at INTEGER);""")

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

async def get_rate(currency):
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(f'https://open.er-api.com/v6/latest/{currency}') as resp:
            resp.raise_for_status()
            data = await resp.json()
            
        if data['result'] != 'success':
            raise ValueError(f"unsupported currency: {currency}")    
        return str(data["rates"]["RUB"])

async def get_rate_cache(currency):
    with closing(sqlite3.connect(RATE_CACHE)) as con:
        cur = con.cursor()
        sql_query = """SELECT rate, fetched_at FROM rate_cache
                        WHERE currency = ?"""
        cur.execute(sql_query, (currency,))
        row = cur.fetchone()
    if row is not None:
        rate, fetched_at = row
        if time.time() - fetched_at < CACHE_TTL:
            return rate
    
    rate = await get_rate(currency)
    with closing(sqlite3.connect(RATE_CACHE)) as con:
        with con:
            cur = con.cursor()
            sql_query = """INSERT INTO rate_cache (currency, rate, fetched_at)
                            VALUES (?, ?, ?) 
                            ON CONFLICT(currency) DO UPDATE    SET rate = excluded.rate, fetched_at = excluded.fetched_at 
                        """
            cur.execute(sql_query, (currency, rate, int(time.time())))
      
    return rate

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
    await message.answer("-Умею здороваться.\n"
                         "- Cобираю статистику: количество уникальных пользователей и их визитов.\n"
                         "- Даю информацию об актуальном курсе валют относительно российского рубля.\n"
                         "- На обычный текст я реагирую как эхо.\n"
                         "Напиши:\n"
                         "/start, чтобы я с тобой поздоровался. Также получишь информацию о количестве своих визитов (сколько раз ты написал /start)\n"
                         "/stats, чтобы увидеть счётчик своих визитов и количество уникальных пользователей бота.\n"
                         "/top, чтобы увидеть топ-5 id пользователей, писавших /start.\n"
                         "/курс USD, чтобы получить стоимость валюты в российских рублях. Замени USD на трёхбуквенный код валюты, которая тебя интересует.\n")

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

@dp.message(Command("курс"))
async def command_rates_handler(message: Message, command: CommandObject) -> None:
    currency = command.args
    if currency:
        upper_currency = currency.strip().upper()
    else:
        await message.answer("Введите трёхбуквенный код валюты.")
        return
   
    try:
        rate = await get_rate_cache(upper_currency)
        await message.answer(f"1 {upper_currency} = {rate} RUB")
    except ValueError:
        await message.answer('Возможно допущена ошибка в наименовании валюты.')
    except aiohttp.ClientError:
        await message.answer("Не удалось получить курс, попробуйте позже.")
    except asyncio.TimeoutError:
        await message.answer('Превышено время ожидания от сервера.')


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    init_db()
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())