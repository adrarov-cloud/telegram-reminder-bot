import asyncio
import logging
import os
import sqlite3
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Получение токена бота
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в файле .env!")
    exit(1)

# Инициализация бота, диспетчера и планировщика
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
scheduler = AsyncIOScheduler()

# Состояния для FSM
class ReminderStates(StatesGroup):
    waiting_for_text = State()
    waiting_for_time = State()

# Инициализация базы данных
def init_db():
    """Создание таблицы для хранения напоминаний"""
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            reminder_text TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_sent INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("✅ База данных инициализирована")

# Парсер времени
def parse_time(time_str: str) -> datetime:
    """Парсинг строки времени в datetime объект"""
    time_str = time_str.lower().strip()
    now = datetime.now()
    
    # Поиск числа в строке
    number_match = re.search(r'\d+', time_str)
    if not number_match:
        raise ValueError("Не найдено число в строке времени")
    
    number = int(number_match.group())
    
    # Определение единицы времени
    if any(word in time_str for word in ['минут', 'мин', 'min', 'minute']):
        return now + timedelta(minutes=number)
    elif any(word in time_str for word in ['час', 'часа', 'часов', 'hour', 'hours']):
        return now + timedelta(hours=number)
    elif any(word in time_str for word in ['день', 'дня', 'дней', 'day', 'days']):
        return now + timedelta(days=number)
    else:
        # По умолчанию считаем минуты
        return now + timedelta(minutes=number)

# Функция отправки напоминания
async def send_reminder(user_id: int, reminder_text: str, reminder_id: int):
    """Отправка напоминания пользователю"""
    try:
        await bot.send_message(
            user_id, 
            f"🔔 **НАПОМИНАНИЕ!**\n\n📝 {reminder_text}\n\n⏰ {datetime.now().strftime('%H:%M')}"
        )
        
        # Отмечаем напоминание как отправленное
        conn = sqlite3.connect('reminders.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE reminders SET is_sent = 1 WHERE id = ?', (reminder_id,))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Напоминание отправлено пользователю {user_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки напоминания: {e}")

# Главное меню
def main_menu():
    """Создание клавиатуры главного меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать напоминание", callback_data="create_reminder")],
        [InlineKeyboardButton(text="📋 Мои напоминания", callback_data="my_reminders")],
        [InlineKeyboardButton(text="🗑 Очистить все", callback_data="clear_all")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, **{user_name}**!\n\n"
        "🤖 Я бот-напоминалка! Помогу тебе не забыть важные дела.\n\n"
        "🎯 **Что я умею:**\n"
        "• Создавать напоминания на любое время\n"
        "• Отправлять уведомления точно в срок\n"
        "• Показывать список всех напоминаний\n"
        "• Работать 24/7 без перерывов\n\n"
        "Выбери действие:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# Создание напоминания
@dp.callback_query(F.data == "create_reminder")
async def start_create_reminder(callback: CallbackQuery, state: FSMContext):
    """Начало создания напоминания"""
    await callback.message.edit_text(
        "📝 **Создание напоминания**\n\n"
        "Введите текст напоминания:\n"
        "*(например: \"Купить молоко\" или \"Встреча с клиентом\")*",
        parse_mode="Markdown"
    )
    await state.set_state(ReminderStates.waiting_for_text)

# Просмотр напоминаний
@dp.callback_query(F.data == "my_reminders")
async def show_my_reminders(callback: CallbackQuery):
    """Показ всех напоминаний пользователя"""
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, reminder_text, reminder_time, is_sent FROM reminders WHERE user_id = ? ORDER BY reminder_time',
        (user_id,)
    )
    reminders = cursor.fetchall()
    conn.close()
    
    if not reminders:
        await callback.message.edit_text(
            "📭 **У вас пока нет напоминаний**\n\n"
            "Создайте первое напоминание!",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
        return
    
    text = "📋 **Ваши напоминания:**\n\n"
    for i, (reminder_id, reminder_text, reminder_time, is_sent) in enumerate(reminders, 1):
        status = "✅ Отправлено" if is_sent else "⏳ Ожидает"
        try:
            dt = datetime.fromisoformat(reminder_time)
            time_formatted = dt.strftime('%d.%m.%Y в %H:%M')
        except:
            time_formatted = reminder_time
        
        text += f"{i}. **{reminder_text}**\n"
        text += f"   ⏰ {time_formatted}\n"
        text += f"   {status}\n\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="Markdown"
    )

# Очистка всех напоминаний
@dp.callback_query(F.data == "clear_all")
async def confirm_clear_all(callback: CallbackQuery):
    """Подтверждение очистки всех напоминаний"""
    await callback.message.edit_text(
        "🗑 **Очистка всех напоминаний**\n\n"
        "Вы уверены, что хотите удалить ВСЕ свои напоминания?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить все", callback_data="confirm_clear")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_menu")]
        ]),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "confirm_clear")
async def clear_all_reminders(callback: CallbackQuery):
    """Удаление всех напоминаний пользователя"""
    user_id = callback.from_user.id
    
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE user_id = ?', (user_id,))
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    await callback.message.edit_text(
        f"✅ **Готово!**\n\nУдалено напоминаний: **{deleted_count}**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="back_to_menu")]
        ]),
        parse_mode="Markdown"
    )

# Помощь
@dp.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    """Показ справки"""
    await callback.message.edit_text(
        "❓ **Справка по боту**\n\n"
        "🔸 **Форматы времени:**\n"
        "• `через 5 минут`\n"
        "• `через 2 часа`\n" 
        "• `через 3 дня`\n\n"
        "🔸 **Примеры использования:**\n"
        "• Купить молоко → через 30 минут\n"
        "• Встреча с врачом → через 2 часа\n"
        "• День рождения мамы → через 5 дней\n\n"
        "💡 **Совет:** Бот работает 24/7 и никогда не забудет напомнить вам!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
        ]),
        parse_mode="Markdown"
    )

# Возврат в главное меню
@dp.callback_query(F.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат в главное меню"""
    user_name = callback.from_user.first_name or "друг"
    await callback.message.edit_text(
        f"👋 Привет, **{user_name}**!\n\n"
        "🤖 Я бот-напоминалка! Выбери действие:",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# FSM: получение текста напоминания
@dp.message(ReminderStates.waiting_for_text)
async def get_reminder_text(message: Message, state: FSMContext):
    """Получение текста напоминания"""
    await state.update_data(reminder_text=message.text)
    
    await message.answer(
        "⏰ **Когда напомнить?**\n\n"
        "Примеры формата:\n"
        "• `через 5 минут`\n"
        "• `через 2 часа`\n"
        "• `через 1 день`\n\n"
        "💡 Просто напишите когда вам напомнить:",
        parse_mode="Markdown"
    )
    await state.set_state(ReminderStates.waiting_for_time)

# FSM: получение времени напоминания
@dp.message(ReminderStates.waiting_for_time)
async def get_reminder_time(message: Message, state: FSMContext):
    """Получение времени напоминания и создание задачи"""
    try:
        data = await state.get_data()
        reminder_text = data['reminder_text']
        
        # Парсинг времени
        reminder_time = parse_time(message.text)
        
        # Проверка, что время в будущем
        if reminder_time <= datetime.now():
            await message.answer(
                "⚠️ **Ошибка!**\n\n"
                "Время должно быть в будущем. Попробуйте еще раз:",
                parse_mode="Markdown"
            )
            return
        
        # Сохранение в базу данных
        conn = sqlite3.connect('reminders.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, username, first_name, reminder_text, reminder_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.first_name or "",
            reminder_text,
            reminder_time.isoformat(),
            datetime.now().isoformat()
        ))
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Добавление задачи в планировщик
        scheduler.add_job(
            send_reminder,
            'date',
            run_date=reminder_time,
            args=[message.from_user.id, reminder_text, reminder_id],
            id=f"reminder_{reminder_id}",
            replace_existing=True
        )
        
        await message.answer(
            "✅ **Напоминание создано!**\n\n"
            f"📝 **Текст:** {reminder_text}\n"
            f"⏰ **Время:** {reminder_time.strftime('%d.%m.%Y в %H:%M')}\n\n"
            f"🔔 Я напомню вам точно в срок!",
            reply_markup=main_menu(),
            parse_mode="Markdown"
        )
        
        logger.info(f"✅ Создано напоминание для {message.from_user.id}: {reminder_text} на {reminder_time}")
        
    except Exception as e:
        await message.answer(
            "❌ **Ошибка в формате времени!**\n\n"
            "Используйте примеры:\n"
            "• `через 30 минут`\n" 
            "• `через 2 часа`\n"
            "• `через 1 день`",
            parse_mode="Markdown"
        )
        logger.error(f"Ошибка парсинга времени '{message.text}': {e}")
        return
    
    await state.clear()

# Команда /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "❓ **Справка по боту**\n\n"
        "Используйте /start для доступа к главному меню",
        parse_mode="Markdown"
    )

# Загрузка ожидающих напоминаний при старте
def load_pending_reminders():
    """Загрузка напоминаний из БД в планировщик при перезапуске бота"""
    conn = sqlite3.connect('reminders.db')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id, user_id, reminder_text, reminder_time FROM reminders WHERE is_sent = 0'
    )
    reminders = cursor.fetchall()
    conn.close()
    
    count = 0
    for reminder_id, user_id, reminder_text, reminder_time in reminders:
        try:
            reminder_dt = datetime.fromisoformat(reminder_time)
            
            # Если время еще не наступило
            if reminder_dt > datetime.now():
                scheduler.add_job(
                    send_reminder,
                    'date',
                    run_date=reminder_dt,
                    args=[user_id, reminder_text, reminder_id],
                    id=f"reminder_{reminder_id}",
                    replace_existing=True
                )
                count += 1
        except Exception as e:
            logger.error(f"Ошибка загрузки напоминания {reminder_id}: {e}")
    
    logger.info(f"✅ Загружено {count} ожидающих напоминаний")

# Главная функция
async def main():
    """Главная функция запуска бота"""
    logger.info("🔧 Инициализация базы данных...")
    init_db()
    
    logger.info("⏰ Запуск планировщика...")
    scheduler.start()
    
    logger.info("📥 Загрузка ожидающих напоминаний...")
    load_pending_reminders()
    
    logger.info("🚀 Запуск бота...")
    logger.info("✅ Бот готов к работе!")
    
    await dp.start_polling(bot, skip_updates=True)

# Точка входа
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}")
    finally:
        logger.info("🔄 Завершение работы...")