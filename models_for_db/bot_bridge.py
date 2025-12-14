import telebot
import requests

# 1. Настройки
TELEGRAM_TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"
DLP_API_URL = "http://localhost:8000/api/scan"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# 2. Обработчик всех сообщений
@bot.message_handler(func=lambda message: True)
def check_message(message):
    user_text = message.text
    user_id = message.from_user.id
    username = message.from_user.username

    print(f"📩 Проверяем: {user_text}")

    try:
        # 3. Отправляем текст в ВАШ DLP BACKEND
        response = requests.post(DLP_API_URL, json={
            "user_id": user_id,
            "content": user_text,
            "source": f"telegram_@{username}"
        })
        
        result = response.json()

        # 4. Если DLP сказал "BLOCKED" -> Удаляем сообщение
        if result.get("result") == "blocked":
            print(f"🚫 БЛОКИРУЕМ! Политика: {result.get('policy')}")
            
            # Удаляем сообщение пользователя
            bot.delete_message(message.chat.id, message.message_id)
            
            # (Опционально) Пишем предупреждение
            bot.send_message(message.chat.id, 
                f"⚠️ @{username}, ваше сообщение удалено системой безопасности!\n"
                f"Причина: {result.get('policy')}")

    except Exception as e:
        print(f"Ошибка проверки: {e}")

# Запуск
print("👮 Бот-цезнзор запущен и охраняет чат...")
bot.polling()
