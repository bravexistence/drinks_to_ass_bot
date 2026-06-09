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

# Латиница, визуально неотличимая от кириллицы (Unicode confusables).
# Покрывает приёмы вида "нaпитки" (Latin a), "Hапитки" (Latin H), "Нaпитки".
VISUAL_LATIN_TO_CYRILLIC = str.maketrans(
    {
        "a": "а",
        "c": "с",
        "e": "е",
        "o": "о",
        "p": "р",
        "x": "х",
        "y": "у",
        "A": "А",
        "B": "В",
        "C": "С",
        "E": "Е",
        "H": "Н",
        "K": "К",
        "M": "М",
        "O": "О",
        "P": "Р",
        "T": "Т",
        "X": "Х",
        "Y": "У",
    }
)

# Простой транслит латиницы → кириллица (ГОСТ-подобный).
# Покрывает приёмы вида "Napitki", "napitok", "NAPITKAMI".
PHONETIC_LATIN_TO_CYRILLIC = str.maketrans(
    {
        "a": "а",
        "b": "б",
        "c": "ц",
        "d": "д",
        "e": "е",
        "f": "ф",
        "g": "г",
        "h": "х",
        "i": "и",
        "j": "й",
        "k": "к",
        "l": "л",
        "m": "м",
        "n": "н",
        "o": "о",
        "p": "п",
        "q": "к",
        "r": "р",
        "s": "с",
        "t": "т",
        "u": "у",
        "v": "в",
        "w": "в",
        "x": "х",
        "y": "ы",
        "z": "з",
        "A": "А",
        "B": "Б",
        "C": "Ц",
        "D": "Д",
        "E": "Е",
        "F": "Ф",
        "G": "Г",
        "H": "Х",
        "I": "И",
        "J": "Й",
        "K": "К",
        "L": "Л",
        "M": "М",
        "N": "Н",
        "O": "О",
        "P": "П",
        "Q": "К",
        "R": "Р",
        "S": "С",
        "T": "Т",
        "U": "У",
        "V": "В",
        "W": "В",
        "X": "Х",
        "Y": "Ы",
        "Z": "З",
    }
)


# Диграфы — обрабатываем ДО посимвольного транслита, иначе 'ch' уйдёт в 'цх'.
TRANSLIT_DIGRAPHS = [
    (re.compile(r"sch", re.IGNORECASE), "щ"),
    (re.compile(r"ch", re.IGNORECASE), "ч"),
    (re.compile(r"sh", re.IGNORECASE), "ш"),
    (re.compile(r"zh", re.IGNORECASE), "ж"),
    (re.compile(r"yo", re.IGNORECASE), "ё"),
    (re.compile(r"yu", re.IGNORECASE), "ю"),
    (re.compile(r"ya", re.IGNORECASE), "я"),
]


def _to_translit(text: str) -> str:
    for pattern, replacement in TRANSLIT_DIGRAPHS:
        text = pattern.sub(replacement, text)
    return text.translate(PHONETIC_LATIN_TO_CYRILLIC)


def is_drinks_mention(text: str) -> bool:
    """Матчит 'напитки' в трёх вариантах: оригинал, визуальные подмены, транслит."""
    candidates = (
        text,
        text.translate(VISUAL_LATIN_TO_CYRILLIC),
        _to_translit(text),
    )
    return any(DRINKS_PATTERN.search(c) for c in candidates)


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
    if payload and is_drinks_mention(payload):
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
