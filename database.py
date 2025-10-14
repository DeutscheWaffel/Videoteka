import os
from peewee import *
from config import DATABASE_URL

# Всегда используем SQLite
def _resolve_sqlite_path(url: str) -> str:
    """Возвращает путь к SQLite файлу из DATABASE_URL или значение по умолчанию."""
    if not url:
        return "videoteka.db"
    # Поддержка форматов: sqlite:///path/to/file.db или просто имя файла
    if url.startswith("sqlite:///"):
        return url.split("sqlite:///")[-1]
    return url

database = SqliteDatabase(_resolve_sqlite_path(DATABASE_URL))

class BaseModel(Model):
    class Meta:
        database = database

class User(BaseModel):
    id = AutoField(primary_key=True)
    username = CharField(max_length=50, unique=True, index=True)
    email = CharField(max_length=100, unique=True, index=True)
    hashed_password = CharField(max_length=255)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    
    class Meta:
        table_name = 'users'

def create_tables():
    """Создает все таблицы в базе данных"""
    database.connect()
    database.create_tables([User], safe=True)
    database.close()

def init_database():
    """Инициализирует базу данных"""
    create_tables()
