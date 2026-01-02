# 📝 Создание файла .env

Файл `.env` защищен от записи (для безопасности). Создайте его вручную:

## Вариант 1: Через терминал (быстро)

```bash
cd /Users/andreykhokhlovskiy/Cursor/wb-reviews-agent
cp .env.template .env
```

## Вариант 2: Вручную через редактор

1. Откройте файл `.env.template` в редакторе
2. Скопируйте все содержимое
3. Создайте новый файл `.env` в корне проекта
4. Вставьте скопированное содержимое
5. Сохраните файл

## Вариант 3: Через команду (все в одной строке)

```bash
cat > .env << 'EOF'
# Wildberries API
WB_API_KEY=eyJhbGciOiJFUzI1NiIsImtpZCI6IjIwMjUwOTA0djEiLCJ0eXAiOiJKV1QifQ.eyJhY2MiOjEsImVudCI6MSwiZXhwIjoxNzgxMTQ2NjgxLCJpZCI6IjAxOWIwOGM0LWVjMzctN2I2YS05ODQ4LWM4OTBiNjhhMGJhOCIsImlpZCI6MjQ0NzAyMywib2lkIjoyNTAwMTk4MDMsInMiOjEyOCwic2lkIjoiNDdlN2QyZWYtZTdiNC00MGE4LWJlZjQtMzg5MTUyM2ZmNmI5IiwidCI6ZmFsc2UsInVpZCI6MjQ0NzAyM30.ctmD7bz6AEJal5liC3w3Dh-CpdHN7fkmhlPQQpQ9X4N8M-Lq26ctV4876sVKneau_NDi4MaBKnugo5iThYTStw
WB_API_URL=https://suppliers-api.wildberries.ru

# OpenRouter API
OPENROUTER_API_KEY=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
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions

# Telegram Bot
TELEGRAM_BOT_TOKEN=8219909377:AAFzGpj2Ztu5WOw1OM1lPohnaAdCOQ9hkFc
TELEGRAM_CHAT_ID=183880583

# Database
DATABASE_URL=sqlite:///./wb_reviews.db

# Scheduler (интервал в секундах, по умолчанию 3600 = 1 час)
SCHEDULER_INTERVAL=3600
EOF
```

## ✅ Проверка

После создания файла проверьте:

```bash
ls -la .env
cat .env  # Должны увидеть ваши ключи
```

## 🔒 Безопасность

- ✅ Файл `.env` уже в `.gitignore` - не попадет в git
- ✅ Не делитесь этим файлом публично
- ✅ На сервере создайте `.env` отдельно с теми же ключами

---

**После создания .env файла:**
1. Установите зависимости: `pip3 install -r requirements.txt`
2. Инициализируйте БД: `python3 init_db.py`
3. Запустите: `python3 main.py`

