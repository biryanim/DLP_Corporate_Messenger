import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv
import httpx

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def scan_via_backend(text: str, user_id: int, channel_id: int) -> dict | None:
    """Отправка сообщения в /api/scan без каких‑либо проверок."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/scan",
            json={
                "text": text,
                "user_id": user_id,
                "channel_id": channel_id,
            },
        )
        if resp.status_code == 200:
            return resp.json()
        return None


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я DLP бот.\n"
        "Я отправляю все сообщения на /api/scan.\n\n"
        "Команды:\n"
        "/incidents — показать последние инциденты."
    )


@dp.message(F.text)
async def handle_text(message: Message):
    """Любое текстовое сообщение отправляется на /api/scan."""
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)
    text = message.text

    logger.info('in here\n\n')
    logger.info(text)

    result = await scan_via_backend(text=text, user_id=user_id, channel_id=chat_id)

    if result and result.get("incidents_found"):
        count = result.get("incidents_count", 0)
        await message.reply(f"Найдено инцидентов: {count}")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
