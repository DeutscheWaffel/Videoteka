from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import init_database, database
from routers import router
from config import HOST, PORT, DEBUG

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация базы данных при запуске
    init_database()
    yield
    # Очистка при завершении (если необходимо)
    pass

# Создание экземпляра FastAPI
app = FastAPI(
    title="Videoteka API",
    description="API для системы видеотеки с аутентификацией",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение/закрытие БД на каждый запрос (для Peewee)
@app.middleware("http")
async def db_session_middleware(request, call_next):
    try:
        if database.is_closed():
            database.connect(reuse_if_open=True)
        response = await call_next(request)
        return response
    finally:
        if not database.is_closed():
            database.close()

# Подключение роутеров
app.include_router(router, prefix="/api/v1")

# Раздача статики и index.html из корня проекта
app.mount("/", StaticFiles(directory=".", html=True), name="static")

@app.get("/health")
async def health_check():
    """Проверка состояния API"""
    return {"status": "healthy", "message": "API работает корректно"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
