# drinks_to_ass_bot

A tiny Telegram bot that replies `#вжопунапитки` whenever someone in the chat mentions any form of the Russian word **«напитки»** (drinks). Built with Python 3.12 and [aiogram 3](https://docs.aiogram.dev/).

## Disclaimer

This is a joke pet project for a small private chat. The detection logic is intentionally **old-school**: no LLM, no ML, no embeddings — just Unicode-confusables normalization, a tiny transliteration table, and one regex. It catches the obvious obfuscation tricks (`Napitki`, `нaпитки`, `Hапитки`, `НAПИТKИ`, …) and stays well under a millisecond per message. If you came looking for production-grade NLP, this is not it.

## Features

- Matches any case form of `напиток` / `напитки` / `напиточек` and their inflections.
- Survives common obfuscations via two normalization passes:
  - **Visual** — Unicode look-alike Latin letters (`a`, `H`, `o`, `p`, …) folded into their Cyrillic counterparts.
  - **Phonetic** — basic GOST-style Latin→Cyrillic transliteration with the common digraphs (`ch`, `sh`, `zh`, `sch`, `yo`, `yu`, `ya`).
- Replies as a Telegram reply to the offending message.
- Reads both `text` and `caption`, so it also triggers on photo/video captions.

## Quick start (local)

You need Python 3.12+ and a bot token from [@BotFather](https://t.me/BotFather). For group chats, turn off **Bot Settings → Group Privacy** in BotFather and re-add the bot to the group (the setting is cached server-side at the moment a bot is added).

```bash
git clone https://github.com/bravexistence/drinks_to_ass_bot.git
cd drinks_to_ass_bot

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# put your BOT_TOKEN into .env

python bot.py
```

## Tests & lint

```bash
pip install pytest ruff
pytest
ruff check .
ruff format --check .
```

48 tests cover the pattern, all obfuscation variants, and the most likely false-positive sources (`drink water`, `напильник`, `напитанный`, …).

## Configuration

| Env var      | Default | Purpose                                         |
| ------------ | ------- | ----------------------------------------------- |
| `BOT_TOKEN`  | —       | Required. From @BotFather.                       |
| `LOG_LEVEL`  | `INFO`  | `DEBUG` / `INFO` / `WARNING` / `ERROR`.          |

## Deployment

Out of scope for this README. There is a `Dockerfile`, a `docker-compose.yml` and a `.github/workflows/cicd.yml` (test → build multi-arch image → push to GHCR → SSH-deploy). Wire up your own server and secrets if you actually want to run this somewhere.

## License

MIT. Use at your own risk and at your friends' expense.
