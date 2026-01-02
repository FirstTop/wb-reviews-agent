# 📝 Шпаргалка по командам

## 🔧 На сервере (VPS)

### Первоначальная настройка
```bash
# Подключение к серверу
ssh user@wb.1mlrd.ru

# Переход в директорию проекта
cd ~/wb-reviews-agent

# Быстрый деплой (автоматически)
./deploy.sh

# Или вручную:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
```

### Управление systemd service
```bash
# Запуск
sudo systemctl start wb-reviews-agent

# Остановка
sudo systemctl stop wb-reviews-agent

# Перезапуск
sudo systemctl restart wb-reviews-agent

# Статус
sudo systemctl status wb-reviews-agent

# Включить автозапуск
sudo systemctl enable wb-reviews-agent

# Отключить автозапуск
sudo systemctl disable wb-reviews-agent
```

### Просмотр логов
```bash
# Все логи
sudo journalctl -u wb-reviews-agent

# Последние 50 строк
sudo journalctl -u wb-reviews-agent -n 50

# В реальном времени (follow)
sudo journalctl -u wb-reviews-agent -f

# За последний час
sudo journalctl -u wb-reviews-agent --since "1 hour ago"

# За сегодня
sudo journalctl -u wb-reviews-agent --since today
```

### Обновление кода
```bash
cd ~/wb-reviews-agent
source venv/bin/activate

# Если используете git
git pull

# Обновить зависимости
pip install -r requirements.txt

# Перезапустить
sudo systemctl restart wb-reviews-agent
```

### Резервное копирование
```bash
cd ~/wb-reviews-agent
cp wb_reviews.db wb_reviews_backup_$(date +%Y%m%d_%H%M%S).db
```

---

## 💻 На локальной машине

### Загрузка на сервер
```bash
# Через rsync (рекомендуется)
rsync -avz --exclude '__pycache__' --exclude '*.pyc' --exclude '.git' \
  /Users/andreykhokhlovskiy/Cursor/wb-reviews-agent/ \
  user@wb.1mlrd.ru:~/wb-reviews-agent/

# Через scp
scp -r * user@wb.1mlrd.ru:~/wb-reviews-agent/
```

### Тестирование локально
```bash
cd /Users/andreykhokhlovskiy/Cursor/wb-reviews-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python init_db.py
python main.py
```

---

## 🌐 Проверка работы

### Через браузер
- Главная: `http://wb.1mlrd.ru:8002/`
- Health: `http://wb.1mlrd.ru:8002/health`
- Статистика: `http://wb.1mlrd.ru:8002/stats`
- API Docs: `http://wb.1mlrd.ru:8002/docs`

### Через curl
```bash
# Health check
curl http://wb.1mlrd.ru:8002/health

# Статистика
curl http://wb.1mlrd.ru:8002/stats

# Ручная обработка отзывов
curl -X POST http://wb.1mlrd.ru:8002/reviews/process
```

---

## 🔍 Диагностика проблем

### Порт занят
```bash
sudo lsof -i :8002
sudo netstat -tulpn | grep 8002
```

### Проверка процессов
```bash
ps aux | grep python
ps aux | grep wb-reviews
```

### Проверка файлов
```bash
ls -la ~/wb-reviews-agent
cat ~/wb-reviews-agent/.env  # Проверьте настройки
```

### Пересоздание БД
```bash
cd ~/wb-reviews-agent
rm wb_reviews.db
source venv/bin/activate
python init_db.py
```

---

## 📱 Telegram

### Получение Chat ID
```bash
# Замените YOUR_BOT_TOKEN на токен бота
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

Или откройте в браузере:
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

---

## 🔐 Безопасность

### Firewall
```bash
# Открыть порт
sudo ufw allow 8002/tcp

# Проверить статус
sudo ufw status
```

### Права доступа
```bash
# Проверить права
ls -la ~/wb-reviews-agent

# Исправить права (если нужно)
chmod 600 ~/wb-reviews-agent/.env
chmod +x ~/wb-reviews-agent/main.py
```

---

## 📊 Мониторинг

### Проверка использования ресурсов
```bash
# CPU и память
top
htop

# Дисковое пространство
df -h
du -sh ~/wb-reviews-agent
```

### Проверка сетевых подключений
```bash
netstat -tulpn | grep 8002
ss -tulpn | grep 8002
```

---

**💡 Совет:** Сохраните этот файл для быстрого доступа к командам!

