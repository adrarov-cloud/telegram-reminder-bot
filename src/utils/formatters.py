"""
Formatters Module

Text formatting utilities for consistent message display
with Markdown support and responsive layouts.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from zoneinfo import ZoneInfo

from src.database.models import Reminder, User, UserStatistics


def format_datetime(dt: datetime, timezone: str = "UTC") -> str:
    """Format datetime for display."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    
    # Convert to user timezone if specified
    if timezone != "UTC":
        try:
            user_tz = ZoneInfo(timezone)
            dt = dt.astimezone(user_tz)
        except:
            pass  # Fallback to UTC
    
    now = datetime.now(dt.tzinfo)
    today = now.date()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    
    date_part = ""
    if dt.date() == today:
        date_part = "сегодня"
    elif dt.date() == tomorrow:
        date_part = "завтра"
    elif dt.date() == yesterday:
        date_part = "вчера"
    else:
        date_part = dt.strftime("%d.%m.%Y")
    
    time_part = dt.strftime("%H:%M")
    
    return f"{date_part} в {time_part}"


def format_time_until(target_time: datetime, now: Optional[datetime] = None) -> str:
    """Format time remaining until target."""
    if now is None:
        now = datetime.utcnow()
    
    if target_time.tzinfo is None:
        target_time = target_time.replace(tzinfo=ZoneInfo("UTC"))
    if now.tzinfo is None:
        now = now.replace(tzinfo=ZoneInfo("UTC"))
    
    delta = target_time - now
    
    if delta.total_seconds() < 0:
        return "просрочено"
    
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"через {days} дн. {hours} ч."
    elif hours > 0:
        return f"через {hours} ч. {minutes} мин."
    elif minutes > 0:
        return f"через {minutes} мин."
    else:
        return "менее минуты"


def format_reminder_preview(
    text: str,
    scheduled_time: datetime,
    original_input: str = "",
    category: Optional[str] = None,
    priority: str = "normal"
) -> str:
    """Format reminder preview for confirmation."""
    preview = f"**📝 Текст:** {text}\n"
    preview += f"**⏰ Время:** {format_datetime(scheduled_time)}\n"
    
    if category:
        category_icons = {
            'work': '💼', 'health': '🏥', 'shopping': '🛒',
            'family': '👨‍👩‍👧‍👦', 'personal': '🎯', 'education': '📚',
            'home': '🏠', 'transport': '🚗'
        }
        icon = category_icons.get(category.lower(), '📁')
        preview += f"**📂 Категория:** {icon} {category.title()}\n"
    
    if priority != "normal":
        priority_icons = {'high': '🔴', 'normal': '🟡', 'low': '🟢'}
        icon = priority_icons.get(priority, '🟡')
        preview += f"**📌 Приоритет:** {icon} {priority.title()}\n"
    
    time_until = format_time_until(scheduled_time)
    if time_until != "просрочено":
        preview += f"**⏳ Осталось:** {time_until}\n"
    
    if original_input:
        preview += f"\n*Ваш ввод: \"{original_input}\"*"
    
    return preview


def format_reminder_details(reminder: Reminder, user_timezone: str = "UTC") -> str:
    """Format detailed reminder information."""
    status_icon = "✅" if reminder.is_sent else "⏳"
    
    message = f"{status_icon} **Напоминание #{reminder.id}**\n\n"
    message += f"📝 **{reminder.title}**\n"
    
    if reminder.description:
        message += f"\n📄 {reminder.description}\n"
    
    message += f"\n⏰ **Время:** {format_datetime(reminder.scheduled_time, user_timezone)}\n"
    
    if reminder.category:
        category_icons = {
            'work': '💼', 'health': '🏥', 'shopping': '🛒',
            'family': '👨‍👩‍👧‍👦', 'personal': '🎯', 'education': '📚',
            'home': '🏠', 'transport': '🚗'
        }
        icon = category_icons.get(reminder.category.lower(), '📁')
        message += f"📂 **Категория:** {icon} {reminder.category.title()}\n"
    
    if reminder.priority != "normal":
        priority_icons = {'high': '🔴', 'normal': '🟡', 'low': '🟢'}
        icon = priority_icons.get(reminder.priority, '🟡')
        message += f"📌 **Приоритет:** {icon} {reminder.priority.title()}\n"
    
    # Status information
    if reminder.is_sent and reminder.sent_at:
        message += f"✅ **Отправлено:** {format_datetime(reminder.sent_at, user_timezone)}\n"
    elif not reminder.is_sent:
        time_until = format_time_until(reminder.scheduled_time)
        if time_until == "просрочено":
            message += "⚠️ **Статус:** Просрочено\n"
        else:
            message += f"⏳ **Осталось:** {time_until}\n"
    
    # Creation info
    message += f"\n📅 **Создано:** {format_datetime(reminder.created_at, user_timezone)}"
    
    return message


def format_reminder_list(
    reminders: List[Reminder], 
    user_timezone: str = "UTC",
    show_status: bool = True
) -> str:
    """Format list of reminders."""
    if not reminders:
        return "📭 **Напоминаний пока нет**\n\nСоздайте первое напоминание!"
    
    message = f"📋 **Ваши напоминания** ({len(reminders)})\n\n"
    
    # Group by status
    active_reminders = [r for r in reminders if not r.is_sent]
    sent_reminders = [r for r in reminders if r.is_sent]
    
    # Show active reminders first
    if active_reminders:
        message += "🔔 **Активные:**\n"
        for i, reminder in enumerate(active_reminders, 1):
            time_until = format_time_until(reminder.scheduled_time)
            status = "⚠️" if time_until == "просрочено" else "⏳"
            
            message += f"{i}. {status} **{reminder.title}**\n"
            message += f"   ⏰ {format_datetime(reminder.scheduled_time, user_timezone)}"
            
            if time_until != "просрочено":
                message += f" ({time_until})"
            
            message += f" • ID #{reminder.id}\n"
    
    # Show completed reminders if any
    if sent_reminders and show_status:
        message += "\n✅ **Выполненные:**\n"
        for reminder in sent_reminders[-3:]:  # Show last 3
            message += f"• **{reminder.title}**\n"
            message += f"  Отправлено: {format_datetime(reminder.sent_at or reminder.scheduled_time, user_timezone)}\n"
    
    return message


def format_user_statistics(stats: UserStatistics) -> str:
    """Format user statistics."""
    message = "📊 **Ваша статистика**\n\n"
    
    # Main metrics
    message += f"📝 **Создано напоминаний:** {stats.total_reminders_created}\n"
    message += f"✅ **Отправлено:** {stats.total_reminders_sent}\n"
    message += f"❌ **Пропущено:** {stats.total_reminders_missed}\n"
    
    # Completion rate
    completion_rate = stats.completion_rate
    if completion_rate >= 90:
        rate_icon = "🟢"
    elif completion_rate >= 70:
        rate_icon = "🟡"
    else:
        rate_icon = "🔴"
    
    message += f"{rate_icon} **Эффективность:** {completion_rate:.1f}%\n"
    
    # Usage stats
    if stats.total_sessions > 0:
        message += f"\n🔄 **Сессий:** {stats.total_sessions}\n"
        message += f"⚙️ **Команд использовано:** {stats.total_commands_used}\n"
        
        avg_commands = stats.total_commands_used / stats.total_sessions
        message += f"📈 **В среднем за сессию:** {avg_commands:.1f} команд\n"
    
    # Time insights
    if stats.average_reminder_lead_time_minutes:
        lead_time_hours = stats.average_reminder_lead_time_minutes / 60
        message += f"\n⏰ **Среднее время планирования:** {lead_time_hours:.1f} часов\n"
    
    if stats.most_active_hour is not None:
        message += f"🕐 **Самое активное время:** {stats.most_active_hour:02d}:00-{stats.most_active_hour+1:02d}:00\n"
    
    # Last update
    message += f"\n📅 **Обновлено:** {format_datetime(stats.last_updated)}"
    
    return message


def format_system_stats(stats: Dict[str, Any]) -> str:
    """Format system statistics."""
    message = "🔧 **Статистика системы**\n\n"
    
    scheduler_stats = stats.get('scheduler', {})
    if scheduler_stats:
        message += f"⏰ **Планировщик:**\n"
        message += f"• Статус: {'🟢 Работает' if scheduler_stats.get('running') else '🔴 Остановлен'}\n"
        message += f"• Активных задач: {scheduler_stats.get('active_jobs', 0)}\n"
        
        job_stats = scheduler_stats.get('stats', {})
        if job_stats:
            message += f"• Выполнено: {job_stats.get('executed', 0)}\n"
            message += f"• Ошибок: {job_stats.get('errors', 0)}\n"
            message += f"• Пропущено: {job_stats.get('missed', 0)}\n"
    
    db_stats = stats.get('database', {})
    if db_stats:
        message += f"\n💾 **База данных:**\n"
        message += f"• Пользователей: {db_stats.get('total_users', 0)}\n"
        message += f"• Активных пользователей: {db_stats.get('active_users', 0)}\n"
        message += f"• Всего напоминаний: {db_stats.get('total_reminders', 0)}\n"
        message += f"• Ожидающих: {db_stats.get('pending_reminders', 0)}\n"
    
    return message


def format_help_message(section: str = "main") -> str:
    """Format help messages."""
    if section == "creating":
        return (
            "📝 **Создание напоминаний**\n\n"
            "**Способы создания:**\n"
            "• ⚡ **Быстро** - одним сообщением\n"
            "• 📋 **Пошагово** - текст, затем время\n"
            "• 🎤 **Голосом** - голосовое сообщение (скоро)\n\n"
            "**Примеры быстрого создания:**\n"
            "• `Купить хлеб через 2 часа`\n"
            "• `Встреча завтра в 15:30`\n"
            "• `Позвонить маме в воскресенье`"
        )
    
    elif section == "time_formats":
        return (
            "⏰ **Форматы времени**\n\n"
            "**Относительное время:**\n"
            "• `через 30 минут`\n"
            "• `через 2 часа`\n"
            "• `через 3 дня`\n"
            "• `через неделю`\n\n"
            "**Абсолютное время:**\n"
            "• `сегодня в 15:30`\n"
            "• `завтра в 9:00`\n"
            "• `в понедельник в 10:00`\n"
            "• `25.12 в 18:00`\n\n"
            "**Специальные:**\n"
            "• `утром` (завтра в 9:00)\n"
            "• `вечером` (сегодня в 18:00)\n"
            "• `потом` (через 2 часа)"
        )
    
    elif section == "managing":
        return (
            "📋 **Управление напоминаниями**\n\n"
            "**Просмотр:**\n"
            "• 📋 Мои напоминания - полный список\n"
            "• Нажмите на напоминание для деталей\n\n"
            "**Действия:**\n"
            "• ✏️ Редактировать текст или время\n"
            "• 📅 Перенести на другое время\n"
            "• 🔔 Отправить сейчас\n"
            "• 🗑 Удалить\n\n"
            "**Массовые операции:**\n"
            "• 🗑 Очистить все - удалить все напоминания\n"
            "• 📊 Статистика - просмотр метрик"
        )
    
    elif section == "settings":
        return (
            "⚙️ **Настройки**\n\n"
            "**Доступные настройки:**\n"
            "• 🌍 **Часовой пояс** - для точного времени\n"
            "• 🔔 **Уведомления** - включить/отключить\n"
            "• 🗑 **Удалить все данные** - полная очистка\n\n"
            "**Автоматические настройки:**\n"
            "• Часовой пояс определяется автоматически\n"
            "• Уведомления включены по умолчанию\n"
            "• Данные сохраняются навсегда"
        )
    
    else:  # main help
        return (
            "❓ **Справка по боту**\n\n"
            "**Главные функции:**\n"
            "• ➕ Создание напоминаний с умным парсингом времени\n"
            "• 📋 Управление списком напоминаний\n"
            "• 📊 Статистика использования\n"
            "• ⚙️ Персональные настройки\n\n"
            "**Быстрый старт:**\n"
            "1. Нажмите ➕ Создать напоминание\n"
            "2. Выберите способ создания\n"
            "3. Следуйте инструкциям\n"
            "4. Получите уведомление в срок!\n\n"
            "💡 Бот понимает естественный язык и работает 24/7"
        )


def escape_markdown(text: str) -> str:
    """Escape special Markdown characters."""
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text


def format_duration(seconds: int) -> str:
    """Format duration in human readable format."""
    if seconds < 60:
        return f"{seconds} сек."
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} мин."
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ч. {minutes} мин."
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days} дн. {hours} ч."
