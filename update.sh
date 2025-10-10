#!/bin/bash

# Скрипт обновления и перезапуска бота
echo "🔄 Обновление бота..."

cd /root/telegram-reminder-bot

# Остановка текущего процесса
echo "⏹️ Остановка текущего бота..."
pkill -f bot.py

# Обновление кода из Git (если используется)
if [ -d ".git" ]; then
    echo "📥 Получение обновлений из Git..."
    git pull origin main
fi

# Активация виртуального окружения
echo "🐍 Активация виртуального окружения..."
source venv/bin/activate

# Обновление зависимостей
echo "📦 Обновление зависимостей..."
pip install -r requirements.txt

# Ожидание завершения предыдущих процессов
sleep 2

# Запуск нового процесса
echo "🚀 Запуск бота..."
nohup python3 bot.py > bot.log 2>&1 &

# Проверка запуска
sleep 3
if pgrep -f "bot.py" > /dev/null; then
    echo "✅ Бот успешно запущен!"
    echo "📄 Логи: tail -f /root/telegram-reminder-bot/bot.log"
else
    echo "❌ Ошибка запуска бота!"
    echo "📄 Проверьте логи: cat /root/telegram-reminder-bot/bot.log"
fi