import os
import threading
import logging
import asyncio
from flask import Flask, Response

# Импортируем вашего бота (предполагается, что основной код в bot.py)
import bot

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Создаём Flask-приложение ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Football Career Simulator Bot is running!"

@app.route('/health')
def health():
    """Эндпоинт для проверки здоровья Render."""
    return Response("OK", status=200)

# --- Функция для запуска вашего бота в отдельном потоке ---
def run_bot():
    logging.info("Запуск Telegram бота в фоновом потоке...")
    # Создаём новый цикл событий для этого потока
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Вызываем функцию main() из вашего bot.py
        bot.main()
    except Exception as e:
        logging.exception(f"Бот остановился с ошибкой: {e}")
    finally:
        loop.close()

# --- Запускаем бота в фоновом потоке ---
bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
logging.info("Фоновый поток для бота запущен.")

# --- Точка входа для Render ---
if __name__ == "main":
    # Render передаёт порт в переменной окружения PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)