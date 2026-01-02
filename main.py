from fastapi import FastAPI
from datetime import datetime
import platform
import sys

app = FastAPI(title="Server Test App", version="1.0.0")


@app.get("/")
def root():
    """Главная страница - проверка работы сервера"""
    return {
        "status": "ok",
        "message": "Сервер работает! 🚀",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "test": "/test",
            "echo": "/echo (POST)"
        }
    }


@app.get("/health")
def health_check():
    """Health check эндпоинт для мониторинга"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/info")
def server_info():
    """Информация о сервере и системе"""
    return {
        "server": {
            "status": "running",
            "timestamp": datetime.now().isoformat()
        },
        "system": {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "processor": platform.processor()
        }
    }


@app.get("/test")
def test_endpoint():
    """Простой тестовый эндпоинт"""
    return {
        "message": "Тест пройден успешно! ✅",
        "timestamp": datetime.now().isoformat(),
        "test_data": {
            "number": 42,
            "text": "Hello, Server!",
            "boolean": True
        }
    }


@app.post("/echo")
def echo(data: dict):
    """Эхо-эндпоинт - возвращает то, что получил (для тестирования POST)"""
    return {
        "message": "Данные получены успешно!",
        "received": data,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Сервер запускается...")
    print("📡 Доступные эндпоинты:")
    print("   - GET  /          - Главная страница")
    print("   - GET  /health    - Health check")
    print("   - GET  /info      - Информация о системе")
    print("   - GET  /test      - Тестовый эндпоинт")
    print("   - POST /echo      - Эхо (отправьте JSON)")
    print("\n🌐 Откройте в браузере: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8000) 