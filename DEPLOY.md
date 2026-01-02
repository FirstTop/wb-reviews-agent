# Инструкция по развертыванию на VPS сервере

## 📋 Что нужно перед началом

1. **Доступ к VPS серверу** (SSH)
2. **API ключи:**
   - Ключ Wildberries API
   - Ключ OpenRouter API
   - Токен Telegram бота
3. **Telegram Chat ID** (как получить - см. ниже)

---

## 🚀 Пошаговая инструкция

### Шаг 1: Подготовка на локальной машине

1. **Убедитесь, что все файлы готовы:**
   ```bash
   cd /Users/andreykhokhlovskiy/Cursor/wb-reviews-agent
   ls -la
   ```

2. **Проверьте, что `.env.example` существует** (если нет - создайте на основе config.py)

---

### Шаг 2: Подключение к серверу

```bash
ssh user@wb.1mlrd.ru
# или
ssh user@<IP_адрес_сервера>
```

Замените `user` на ваше имя пользователя на сервере.

---

### Шаг 3: Подготовка на сервере

1. **Создайте директорию для проекта:**
   ```bash
   mkdir -p ~/wb-reviews-agent
   cd ~/wb-reviews-agent
   ```

2. **Установите Python 3.10+ (если еще не установлен):**
   ```bash
   python3 --version
   # Если версия < 3.10, установите новую версию
   ```

3. **Установите pip и venv:**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv -y
   ```

---

### Шаг 4: Загрузка файлов на сервер

**Вариант A: Через git (рекомендуется)**
```bash
# На сервере
cd ~/wb-reviews-agent
git clone <ваш_репозиторий> .
# или если уже есть репозиторий
git pull
```

**Вариант B: Через scp (если нет git)**
```bash
# На ЛОКАЛЬНОЙ машине
cd /Users/andreykhokhlovskiy/Cursor/wb-reviews-agent
scp -r * user@wb.1mlrd.ru:~/wb-reviews-agent/
```

**Вариант C: Через rsync (лучше для обновлений)**
```bash
# На ЛОКАЛЬНОЙ машине
rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
  /Users/andreykhokhlovskiy/Cursor/wb-reviews-agent/ \
  user@wb.1mlrd.ru:~/wb-reviews-agent/
```

---

### Шаг 5: Настройка окружения на сервере

1. **Создайте виртуальное окружение:**
   ```bash
   cd ~/wb-reviews-agent
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Установите зависимости:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Создайте файл `.env`:**
   ```bash
   nano .env
   # или
   vi .env
   ```

4. **Заполните `.env` файл:**
   ```env
   # Wildberries API
   WB_API_KEY=ваш_ключ_wb_api
   WB_API_URL=https://suppliers-api.wildberries.ru

   # OpenRouter API
   OPENROUTER_API_KEY=ваш_ключ_openrouter
   OPENROUTER_MODEL=openai/gpt-4o-mini
   OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions

   # Telegram Bot
   TELEGRAM_BOT_TOKEN=ваш_токен_telegram_бота
   TELEGRAM_CHAT_ID=ваш_chat_id

   # Database
   DATABASE_URL=sqlite:///./wb_reviews.db

   # Scheduler (интервал в секундах, 3600 = 1 час)
   SCHEDULER_INTERVAL=3600
   ```

5. **Сохраните файл** (Ctrl+X, затем Y, затем Enter для nano)

---

### Шаг 6: Инициализация базы данных

```bash
cd ~/wb-reviews-agent
source venv/bin/activate
python init_db.py
```

Должно появиться: `✅ База данных успешно инициализирована!`

---

### Шаг 7: Тестовый запуск

```bash
cd ~/wb-reviews-agent
source venv/bin/activate
python main.py
```

Проверьте:
- Откройте в браузере: `http://wb.1mlrd.ru:8002/`
- Должна быть страница с информацией о сервере
- Проверьте `/health` и `/stats`

**Остановите сервер** (Ctrl+C) после проверки.

---

### Шаг 8: Настройка автозапуска (systemd)

1. **Создайте systemd service файл:**
   ```bash
   sudo nano /etc/systemd/system/wb-reviews-agent.service
   ```

2. **Вставьте следующее содержимое:**
   ```ini
   [Unit]
   Description=WB Reviews Agent Service
   After=network.target

   [Service]
   Type=simple
   User=ваш_пользователь
   WorkingDirectory=/home/ваш_пользователь/wb-reviews-agent
   Environment="PATH=/home/ваш_пользователь/wb-reviews-agent/venv/bin"
   ExecStart=/home/ваш_пользователь/wb-reviews-agent/venv/bin/python main.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

   **Важно:** Замените `ваш_пользователь` на реальное имя пользователя!

3. **Перезагрузите systemd:**
   ```bash
   sudo systemctl daemon-reload
   ```

4. **Включите автозапуск:**
   ```bash
   sudo systemctl enable wb-reviews-agent
   ```

5. **Запустите сервис:**
   ```bash
   sudo systemctl start wb-reviews-agent
   ```

6. **Проверьте статус:**
   ```bash
   sudo systemctl status wb-reviews-agent
   ```

7. **Просмотр логов:**
   ```bash
   sudo journalctl -u wb-reviews-agent -f
   ```

---

### Шаг 9: Настройка firewall (если нужно)

Если порт 8002 закрыт, откройте его:

```bash
sudo ufw allow 8002/tcp
# или для iptables
sudo iptables -A INPUT -p tcp --dport 8002 -j ACCEPT
```

---

## 🔧 Полезные команды

### Управление сервисом:
```bash
# Запуск
sudo systemctl start wb-reviews-agent

# Остановка
sudo systemctl stop wb-reviews-agent

# Перезапуск
sudo systemctl restart wb-reviews-agent

# Статус
sudo systemctl status wb-reviews-agent

# Логи
sudo journalctl -u wb-reviews-agent -f
sudo journalctl -u wb-reviews-agent --since "1 hour ago"
```

### Обновление кода:
```bash
cd ~/wb-reviews-agent
source venv/bin/activate

# Если используете git
git pull

# Переустановка зависимостей (если изменились)
pip install -r requirements.txt

# Перезапуск сервиса
sudo systemctl restart wb-reviews-agent
```

### Резервное копирование БД:
```bash
cd ~/wb-reviews-agent
cp wb_reviews.db wb_reviews_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## 📱 Как получить Telegram Chat ID

1. Создайте бота через [@BotFather](https://t.me/botfather):
   - Отправьте `/newbot`
   - Следуйте инструкциям
   - Сохраните токен бота

2. Напишите боту любое сообщение

3. Получите Chat ID:
   ```bash
   curl https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
   ```
   
   Или откройте в браузере:
   ```
   https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
   ```

4. Найдите в ответе `"chat":{"id":123456789}` - это ваш Chat ID

---

## 🐛 Решение проблем

### Сервис не запускается:
```bash
# Проверьте логи
sudo journalctl -u wb-reviews-agent -n 50

# Проверьте права доступа
ls -la ~/wb-reviews-agent
chmod +x ~/wb-reviews-agent/main.py
```

### Порт занят:
```bash
# Проверьте, что использует порт 8002
sudo lsof -i :8002
# или
sudo netstat -tulpn | grep 8002
```

### Ошибки с БД:
```bash
# Пересоздайте БД
cd ~/wb-reviews-agent
rm wb_reviews.db
python init_db.py
```

### Проблемы с зависимостями:
```bash
cd ~/wb-reviews-agent
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

---

## ✅ Проверка работоспособности

После запуска проверьте:

1. **Главная страница:**
   ```
   http://wb.1mlrd.ru:8002/
   ```

2. **Health check:**
   ```
   http://wb.1mlrd.ru:8002/health
   ```

3. **Статистика:**
   ```
   http://wb.1mlrd.ru:8002/stats
   ```

4. **API документация:**
   ```
   http://wb.1mlrd.ru:8002/docs
   ```

5. **Логи сервиса:**
   ```bash
   sudo journalctl -u wb-reviews-agent -f
   ```

---

## 📝 Следующие шаги

1. ✅ Сервер запущен и работает
2. ✅ Проверьте, что планировщик работает (ждет час до первой проверки)
3. ✅ Настройте мониторинг (опционально)
4. ✅ Настройте резервное копирование БД (cron job)

---

## 🔒 Безопасность

- ✅ Не коммитьте `.env` файл в git
- ✅ Используйте сильные пароли для API ключей
- ✅ Ограничьте доступ к порту 8002 (firewall)
- ✅ Регулярно обновляйте зависимости
- ✅ Делайте резервные копии БД

---

**Готово!** Ваш сервис должен работать на `http://wb.1mlrd.ru:8002/`

