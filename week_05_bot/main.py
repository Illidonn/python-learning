import asyncio
import logging
import sys
import json
from pathlib import Path

from aiogram import Bot, Dispatcher, html, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import BOT_TOKEN


BASE_DIR = Path(__file__).resolve().parent
VISITS_FILE = BASE_DIR / "visits.json"

dp = Dispatcher()


def track_visit(filename, user_id):
    user_id = str(user_id)
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    data[user_id] = data.get(user_id, 0) + 1

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data[user_id]

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
    num_visit = track_visit(VISITS_FILE, message.from_user.id)
    await message.answer(f"Привет, {html.bold(message.from_user.full_name)}! Номер твоего визита к данному боту - {num_visit}")

@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    """
    Этот хендлер получает сообщение от команды пользователя `/help`
    """
    await message.answer("Сейчас я умею только здороваться. Напиши /start, чтобы я с тобой поздоровался.")


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())