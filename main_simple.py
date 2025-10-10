import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

# Загружаем переменные из .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    exit(1)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🤖 Привет! Я бот-напоминалка!\n\n"
        "Доступные команды:\n"
        "/start - запуск бота\n" 
        "/help - справка\n"
        "/test - тестовое сообщение"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("📖 Справка по боту-напоминалке")

@dp.message(Command("test"))
async def cmd_test(message: Message):
    await message.answer("✅ Тест прошел успешно! Бот работает!")

async def main():
    logger.info("🚀 Запускаем бота...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
