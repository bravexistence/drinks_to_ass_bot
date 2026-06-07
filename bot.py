import asyncio
import logging
import os
import re
import sys

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
REPLY_TEXT = "#вжопунапитки"

DRINKS_PATTERN = re.compile(
    r"\bнапит(ок|к[а-яё]+|очек|очк[а-яё]+)\b",
    re.IGNORECASE,
)

dp = Dispatcher()


@dp.message(F.text | F.caption)
async def handle_text(message: Message) -> None:
    payload = message.text or message.caption
    logging.info(
        "MSG chat_id=%s chat_type=%s from=%s text=%r caption=%r",
        message.chat.id,
        message.chat.type,
        message.from_user.username if message.from_user else None,
        message.text,
        message.caption,
    )
    if payload and DRINKS_PATTERN.search(payload):
        await message.reply(REPLY_TEXT)


@dp.message()
async def fallback(message: Message) -> None:
    logging.warning(
        "UNHANDLED MSG chat_id=%s chat_type=%s content_type=%s from=%s raw=%s",
        message.chat.id,
        message.chat.type,
        message.content_type,
        message.from_user.username if message.from_user else None,
        message.model_dump(exclude_none=True),
    )


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    if not BOT_TOKEN:
        logging.error("BOT_TOKEN не задан. Положи токен в .env или переменную окружения.")
        sys.exit(1)

    bot = Bot(token=BOT_TOKEN)

    try:
        me = await bot.get_me()
    except TelegramUnauthorizedError:
        logging.error("Telegram API отверг токен (401 Unauthorized). Проверь BOT_TOKEN в .env.")
        await bot.session.close()
        sys.exit(1)
    except TelegramNetworkError as exc:
        logging.error("Не удалось достучаться до Telegram API: %s", exc)
        await bot.session.close()
        sys.exit(1)

    logging.info(
        "Подключено к Telegram как @%s (id=%d, name=%r). Запускаю long polling...",
        me.username,
        me.id,
        me.full_name,
    )
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
