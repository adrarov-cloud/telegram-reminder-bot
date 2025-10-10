import sqlite3
from datetime import datetime, timedelta
import re
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not found!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

class ReminderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

def init_db():
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            reminder_text TEXT,
            reminder_time TEXT,
            is_sent INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
def parse_time(time_str: str) -> datetime:
    time_str = time_str.lower().strip()
    now = datetime.now()
    
    if "минут" in time_str or "min" in time_str:
        minutes = int(re.search(r'\d+', time_str).group())
        return now + timedelta(minutes=minutes)
    elif "час" in time_str or "hour" in time_str:
        hours = int(re.search(r'\d+', time_str).group())
        return now + timedelta(hours=hours)
    
    raise ValueError("Неизвестный формат времени")

async def send_reminder(user_id: int, reminder_text: str, reminder_id: int):
    try:
        await bot.send_message(user_id, f"?? НАПОМИНАНИЕ!\n\n{reminder_text}")
        
        conn = sqlite3.connect('reminders.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE reminders SET is_sent = 1 WHERE id = ?', (reminder_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка отправки: {e}")

@dp.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Create reminder", callback_data="create")],
        [InlineKeyboardButton(text="Help", callback_data="help")]
    ])
    
    await message.answer(
        f"Hello {message.from_user.first_name}!\n\n"
        "I'm your reminder bot! Choose an action:",
        reply_markup=keyboard
    )

@dp.callback_query()
async def process_callback(callback_query):
    if callback_query.data == "create":
        await callback_query.message.answer("Feature coming soon! Bot is working!")
    elif callback_query.data == "help":
        await callback_query.message.answer("This is a reminder bot. Use /start to begin.")

async def main():
    logger.info("Starting bot...")
    logger.info("Bot is ready!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
