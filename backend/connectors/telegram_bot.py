import asyncio
import os
import io
from pathlib import Path
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, Document
from dotenv import load_dotenv
import httpx

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Извлекает текст из файла по расширению"""
    ext = Path(filename).suffix.lower()
    
    try:
        if ext == ".txt":
            return file_bytes.decode("utf-8", errors="ignore")
        
        elif ext == ".pdf" and PdfReader:
            pdf = PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text
        
        elif ext == ".docx" and DocxDocument:
            doc = DocxDocument(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        
        else:
            return f"[Формат {ext} не поддерживается]"
    
    except Exception as e:
        return f"[Ошибка при чтении файла: {e}]"


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


    result = await scan_via_backend(text=text, user_id=user_id, channel_id=chat_id)

    if result and result.get("incidents_found"):
        count = result.get("incidents_count", 0)
        try:
            await message.delete()
            await message.answer(
                f"🚫 Сообщение от {message.from_user.mention_html()} удалено\n"
                f"Причина: обнаружены конфиденциальные данные ({count} нарушений)",
                parse_mode="HTML"
            )
        except Exception:
            await message.reply(f"⚠️ Найдено инцидентов: {count}")


@dp.message(F.document)
async def handle_document(message: Message):
    """Обработка документов"""
    document: Document = message.document
    user_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if document.file_size > 20 * 1024 * 1024:
        await message.reply("⚠️ Файл слишком большой (максимум 20 МБ)")
        return
    
    file = await bot.get_file(document.file_id)
    file_bytes = await bot.download_file(file.file_path)
    
    text = extract_text_from_file(file_bytes.read(), document.file_name)
    
    if not text or text.startswith("["):
        await message.reply(f"⚠️ {text}")
        return
    
    result = await scan_via_backend(text=text, user_id=user_id, channel_id=chat_id)
    
    if result and result.get("incidents_found"):
        count = result.get("incidents_count", 0)
        
        try:
            await message.delete()
            await message.answer(
                f"🚫 Документ <b>{document.file_name}</b> удалён\n"
                f"Причина: обнаружены конфиденциальные данные ({count} нарушений)",
                parse_mode="HTML"
            )
        except Exception:
            await message.reply(
                f"⚠️ В документе найдены конфиденциальные данные: {count} нарушений"
            )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
