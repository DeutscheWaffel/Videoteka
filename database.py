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
    avatar_base64 = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    
    class Meta:
        table_name = 'users'

class Bookmark(BaseModel):
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref='bookmarks', on_delete='CASCADE')
    movie_id = CharField(max_length=100, index=True)
    title = CharField(max_length=255)
    author = CharField(max_length=255, null=True)
    price = CharField(max_length=50, null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        table_name = 'bookmarks'
        indexes = (
            # Уникальность закладки по пользователю и идентификатору фильма
            (('user', 'movie_id'), True),
        )

def create_tables():
    """Создает все таблицы в базе данных"""
    database.connect()
    database.create_tables([User, Bookmark], safe=True)
    database.close()

def init_database():
    """Инициализирует базу данных"""
    create_tables()
    # Простая миграция: добавим колонку avatar_base64, если её нет
    database.connect(reuse_if_open=True)
    try:
        info = database.execute_sql("PRAGMA table_info(users)").fetchall()
        columns = {row[1] for row in info}
        if 'avatar_base64' not in columns:
            database.execute_sql("ALTER TABLE users ADD COLUMN avatar_base64 TEXT")
    finally:
        if not database.is_closed():
            database.close()
