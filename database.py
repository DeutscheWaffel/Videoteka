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

class CartItem(BaseModel):
    id = AutoField(primary_key=True)
    user = ForeignKeyField(User, backref='cart_items', on_delete='CASCADE')
    movie_id = CharField(max_length=100, index=True)
    title = CharField(max_length=255)
    author = CharField(max_length=255, null=True)
    price = CharField(max_length=50, null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        table_name = 'cart_items'
        indexes = (
            (('user', 'movie_id'), True),
        )

class Film(BaseModel):
    flim_id = AutoField(primary_key=True, column_name='flim_id')
    title = CharField(max_length=255)
    title_ru = CharField(max_length=255, null=True, column_name='title-ru')
    author = CharField(max_length=255, null=True)
    price = CharField(max_length=50, null=True)
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    genre_title = CharField(max_length=100, column_name='genre-title')

    class Meta:
        table_name = 'film_list'

def create_tables():
    """Создает все таблицы в базе данных"""
    database.connect()
    database.create_tables([User, Bookmark, CartItem, Film], safe=True)
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
        # Создадим таблицу корзины, если её нет
        database.create_tables([CartItem, Film], safe=True)
 
        # Миграция: добавить колонку title-ru, если её нет
        film_info = database.execute_sql("PRAGMA table_info(film_list)").fetchall()
        film_columns = {row[1] for row in film_info}
        if 'title-ru' not in film_columns:
            database.execute_sql("ALTER TABLE film_list ADD COLUMN \"title-ru\" TEXT")

        # Засеем таблицу фильмов, если она пуста
        try:
            if Film.select().limit(1).count() == 0:
                films = [
                    {"title": "The Shawshank Redemption", "title_ru": "Побег из Шоушенка", "author": "Frank Darabont", "price": "599", "genre_title": "Drama"},
                    {"title": "The Godfather", "title_ru": "Крёстный отец", "author": "Francis Ford Coppola", "price": "699", "genre_title": "Crime"},
                    {"title": "The Dark Knight", "title_ru": "Тёмный рыцарь", "author": "Christopher Nolan", "price": "649", "genre_title": "Action"},
                    {"title": "Pulp Fiction", "title_ru": "Криминальное чтиво", "author": "Quentin Tarantino", "price": "499", "genre_title": "Crime"},
                    {"title": "The Lord of the Rings: The Return of the King", "title_ru": "Властелин колец: Возвращение короля", "author": "Peter Jackson", "price": "799", "genre_title": "Fantasy"},
                    {"title": "Fight Club", "title_ru": "Бойцовский клуб", "author": "David Fincher", "price": "449", "genre_title": "Drama"},
                    {"title": "Forrest Gump", "title_ru": "Форрест Гамп", "author": "Robert Zemeckis", "price": "449", "genre_title": "Drama"},
                    {"title": "Inception", "title_ru": "Начало", "author": "Christopher Nolan", "price": "649", "genre_title": "Sci-Fi"},
                    {"title": "The Matrix", "title_ru": "Матрица", "author": "The Wachowskis", "price": "499", "genre_title": "Sci-Fi"},
                    {"title": "Goodfellas", "title_ru": "Славные парни", "author": "Martin Scorsese", "price": "549", "genre_title": "Crime"},
                    {"title": "Se7en", "title_ru": "Семь", "author": "David Fincher", "price": "499", "genre_title": "Thriller"},
                    {"title": "Interstellar", "title_ru": "Интерстеллар", "author": "Christopher Nolan", "price": "699", "genre_title": "Sci-Fi"},
                    {"title": "Parasite", "title_ru": "Паразиты", "author": "Bong Joon-ho", "price": "549", "genre_title": "Thriller"},
                    {"title": "Whiplash", "title_ru": "Одержимость", "author": "Damien Chazelle", "price": "449", "genre_title": "Drama"},
                    {"title": "The Silence of the Lambs", "title_ru": "Молчание ягнят", "author": "Jonathan Demme", "price": "499", "genre_title": "Thriller"},
                    {"title": "The Green Mile", "title_ru": "Зелёная миля", "author": "Frank Darabont", "price": "499", "genre_title": "Drama"},
                    {"title": "Saving Private Ryan", "title_ru": "Спасти рядового Райана", "author": "Steven Spielberg", "price": "599", "genre_title": "War"},
                    {"title": "The Prestige", "title_ru": "Престиж", "author": "Christopher Nolan", "price": "499", "genre_title": "Drama"},
                    {"title": "Gladiator", "title_ru": "Гладиатор", "author": "Ridley Scott", "price": "499", "genre_title": "Action"},
                    {"title": "The Lion King", "title_ru": "Король Лев", "author": "Roger Allers, Rob Minkoff", "price": "449", "genre_title": "Animation"},
                    {"title": "The Avengers", "title_ru": "Мстители", "author": "Joss Whedon", "price": "549", "genre_title": "Action"},
                    {"title": "Titanic", "title_ru": "Титаник", "author": "James Cameron", "price": "599", "genre_title": "Romance"},
                    {"title": "Jurassic Park", "title_ru": "Парк юрского периода", "author": "Steven Spielberg", "price": "499", "genre_title": "Adventure"},
                    {"title": "Star Wars: A New Hope", "title_ru": "Звёздные войны: Новая надежда", "author": "George Lucas", "price": "499", "genre_title": "Sci-Fi"},
                    {"title": "The Empire Strikes Back", "title_ru": "Империя наносит ответный удар", "author": "Irvin Kershner", "price": "499", "genre_title": "Sci-Fi"},
                    {"title": "Return of the Jedi", "title_ru": "Возвращение джедая", "author": "Richard Marquand", "price": "499", "genre_title": "Sci-Fi"},
                    {"title": "The Lord of the Rings: The Fellowship of the Ring", "title_ru": "Властелин колец: Братство Кольца", "author": "Peter Jackson", "price": "779", "genre_title": "Fantasy"},
                    {"title": "The Lord of the Rings: The Two Towers", "title_ru": "Властелин колец: Две крепости", "author": "Peter Jackson", "price": "779", "genre_title": "Fantasy"},
                    {"title": "The Departed", "title_ru": "Отступники", "author": "Martin Scorsese", "price": "549", "genre_title": "Crime"},
                    {"title": "Django Unchained", "title_ru": "Джанго освобождённый", "author": "Quentin Tarantino", "price": "549", "genre_title": "Western"},
                    {"title": "Inglourious Basterds", "title_ru": "Бесславные ублюдки", "author": "Quentin Tarantino", "price": "549", "genre_title": "War"},
                    {"title": "Braveheart", "title_ru": "Храброе сердце", "author": "Mel Gibson", "price": "499", "genre_title": "Historical"},
                    {"title": "Avatar", "title_ru": "Аватар", "author": "James Cameron", "price": "649", "genre_title": "Sci-Fi"},
                    {"title": "The Social Network", "title_ru": "Социальная сеть", "author": "David Fincher", "price": "499", "genre_title": "Drama"},
                    {"title": "Mad Max: Fury Road", "title_ru": "Безумный Макс: Дорога ярости", "author": "George Miller", "price": "549", "genre_title": "Action"},
                    {"title": "Joker", "title_ru": "Джокер", "author": "Todd Phillips", "price": "549", "genre_title": "Drama"},
                    {"title": "Toy Story", "title_ru": "История игрушек", "author": "John Lasseter", "price": "399", "genre_title": "Animation"},
                    {"title": "Up", "title_ru": "Вверх", "author": "Pete Docter", "price": "399", "genre_title": "Animation"},
                    {"title": "WALL-E", "title_ru": "ВАЛЛ•И", "author": "Andrew Stanton", "price": "399", "genre_title": "Animation"},
                    {"title": "Spirited Away", "title_ru": "Унесённые призраками", "author": "Hayao Miyazaki", "price": "499", "genre_title": "Animation"},
                    {"title": "Your Name", "title_ru": "Твоё имя", "author": "Makoto Shinkai", "price": "499", "genre_title": "Animation"},
                    {"title": "City of God", "title_ru": "Город Бога", "author": "Fernando Meirelles", "price": "499", "genre_title": "Crime"},
                    {"title": "Oldboy", "title_ru": "Олдбой", "author": "Park Chan-wook", "price": "499", "genre_title": "Thriller"},
                    {"title": "Alien", "title_ru": "Чужой", "author": "Ridley Scott", "price": "499", "genre_title": "Horror"},
                    {"title": "Aliens", "title_ru": "Чужие", "author": "James Cameron", "price": "499", "genre_title": "Sci-Fi"},
                    {"title": "Terminator 2: Judgment Day", "title_ru": "Терминатор 2: Судный день", "author": "James Cameron", "price": "499", "genre_title": "Action"},
                    {"title": "Back to the Future", "title_ru": "Назад в будущее", "author": "Robert Zemeckis", "price": "449", "genre_title": "Sci-Fi"},
                    {"title": "Rocky", "title_ru": "Рокки", "author": "John G. Avildsen", "price": "449", "genre_title": "Drama"},
                    {"title": "The Pianist", "title_ru": "Пианист", "author": "Roman Polanski", "price": "499", "genre_title": "Drama"},
                    {"title": "Amélie", "title_ru": "Амели", "author": "Jean-Pierre Jeunet", "price": "449", "genre_title": "Romance"}
                ]
                Film.insert_many(films).execute()
        except Exception:
            # Не прерываем инициализацию, если сид не прошёл
            pass

        # Бэкфилл существующих записей, если были внесены ранее без title-ru и рублевых цен
        try:
            updates = {
                "The Shawshank Redemption": ("Побег из Шоушенка", "599"),
                "The Godfather": ("Крёстный отец", "699"),
                "The Dark Knight": ("Тёмный рыцарь", "649"),
                "Pulp Fiction": ("Криминальное чтиво", "499"),
                "The Lord of the Rings: The Return of the King": ("Властелин колец: Возвращение короля", "799"),
                "Fight Club": ("Бойцовский клуб", "449"),
                "Forrest Gump": ("Форрест Гамп", "449"),
                "Inception": ("Начало", "649"),
                "The Matrix": ("Матрица", "499"),
                "Goodfellas": ("Славные парни", "549"),
                "Se7en": ("Семь", "499"),
                "Interstellar": ("Интерстеллар", "699"),
                "Parasite": ("Паразиты", "549"),
                "Whiplash": ("Одержимость", "449"),
                "The Silence of the Lambs": ("Молчание ягнят", "499"),
                "The Green Mile": ("Зелёная миля", "499"),
                "Saving Private Ryan": ("Спасти рядового Райана", "599"),
                "The Prestige": ("Престиж", "499"),
                "Gladiator": ("Гладиатор", "499"),
                "The Lion King": ("Король Лев", "449"),
                "The Avengers": ("Мстители", "549"),
                "Titanic": ("Титаник", "599"),
                "Jurassic Park": ("Парк юрского периода", "499"),
                "Star Wars: A New Hope": ("Звёздные войны: Новая надежда", "499"),
                "The Empire Strikes Back": ("Империя наносит ответный удар", "499"),
                "Return of the Jedi": ("Возвращение джедая", "499"),
                "The Lord of the Rings: The Fellowship of the Ring": ("Властелин колец: Братство Кольца", "779"),
                "The Lord of the Rings: The Two Towers": ("Властелин колец: Две крепости", "779"),
                "The Departed": ("Отступники", "549"),
                "Django Unchained": ("Джанго освобождённый", "549"),
                "Inglourious Basterds": ("Бесславные ублюдки", "549"),
                "Braveheart": ("Храброе сердце", "499"),
                "Avatar": ("Аватар", "649"),
                "The Social Network": ("Социальная сеть", "499"),
                "Mad Max: Fury Road": ("Безумный Макс: Дорога ярости", "549"),
                "Joker": ("Джокер", "549"),
                "Toy Story": ("История игрушек", "399"),
                "Up": ("Вверх", "399"),
                "WALL-E": ("ВАЛЛ•И", "399"),
                "Spirited Away": ("Унесённые призраками", "499"),
                "Your Name": ("Твоё имя", "499"),
                "City of God": ("Город Бога", "499"),
                "Oldboy": ("Олдбой", "499"),
                "Alien": ("Чужой", "499"),
                "Aliens": ("Чужие", "499"),
                "Terminator 2: Judgment Day": ("Терминатор 2: Судный день", "499"),
                "Back to the Future": ("Назад в будущее", "449"),
                "Rocky": ("Рокки", "449"),
                "The Pianist": ("Пианист", "499"),
                "Amélie": ("Амели", "449"),
            }
            for film in Film.select():
                if film.title in updates:
                    ru, rub = updates[film.title]
                    if film.title_ru != ru or film.price != rub:
                        film.title_ru = ru
                        film.price = rub
                        film.save()
        except Exception:
            pass

        # Приведение жанров к допустимому набору и сокращение до 25 фильмов (>=3 на жанр)
        try:
            # Полная переинициализация списка фильмов согласно требованиям
            curated = [
                # action (4)
                {"title": "The Dark Knight", "title_ru": "Тёмный рыцарь", "author": "Christopher Nolan", "price": "649", "genre_title": "action"},
                {"title": "Gladiator", "title_ru": "Гладиатор", "author": "Ridley Scott", "price": "499", "genre_title": "action"},
                {"title": "The Avengers", "title_ru": "Мстители", "author": "Joss Whedon", "price": "549", "genre_title": "action"},
                {"title": "Terminator 2: Judgment Day", "title_ru": "Терминатор 2: Судный день", "author": "James Cameron", "price": "499", "genre_title": "action"},

                # comedy (4)
                {"title": "Toy Story", "title_ru": "История игрушек", "author": "John Lasseter", "price": "399", "genre_title": "comedy"},
                {"title": "Up", "title_ru": "Вверх", "author": "Pete Docter", "price": "399", "genre_title": "comedy"},
                {"title": "Amélie", "title_ru": "Амели", "author": "Jean-Pierre Jeunet", "price": "449", "genre_title": "comedy"},
                {"title": "The Lion King", "title_ru": "Король Лев", "author": "Roger Allers, Rob Minkoff", "price": "449", "genre_title": "comedy"},

                # drama (4)
                {"title": "The Shawshank Redemption", "title_ru": "Побег из Шоушенка", "author": "Frank Darabont", "price": "599", "genre_title": "drama"},
                {"title": "Fight Club", "title_ru": "Бойцовский клуб", "author": "David Fincher", "price": "449", "genre_title": "drama"},
                {"title": "Forrest Gump", "title_ru": "Форрест Гамп", "author": "Robert Zemeckis", "price": "449", "genre_title": "drama"},
                {"title": "The Green Mile", "title_ru": "Зелёная миля", "author": "Frank Darabont", "price": "499", "genre_title": "drama"},

                # fantasy (4)
                {"title": "The Lord of the Rings: The Fellowship of the Ring", "title_ru": "Властелин колец: Братство Кольца", "author": "Peter Jackson", "price": "779", "genre_title": "fantasy"},
                {"title": "The Lord of the Rings: The Two Towers", "title_ru": "Властелин колец: Две крепости", "author": "Peter Jackson", "price": "779", "genre_title": "fantasy"},
                {"title": "The Lord of the Rings: The Return of the King", "title_ru": "Властелин колец: Возвращение короля", "author": "Peter Jackson", "price": "799", "genre_title": "fantasy"},
                {"title": "Spirited Away", "title_ru": "Унесённые призраками", "author": "Hayao Miyazaki", "price": "499", "genre_title": "fantasy"},

                # horror (4)
                {"title": "Alien", "title_ru": "Чужой", "author": "Ridley Scott", "price": "499", "genre_title": "horror"},
                {"title": "The Conjuring", "title_ru": "Заклятие", "author": "James Wan", "price": "499", "genre_title": "horror"},
                {"title": "The Conjuring 2", "title_ru": "Заклятие 2", "author": "James Wan", "price": "499", "genre_title": "horror"},
                {"title": "The Silence of the Lambs", "title_ru": "Молчание ягнят", "author": "Jonathan Demme", "price": "499", "genre_title": "horror"},

                # scifi (5)
                {"title": "Inception", "title_ru": "Начало", "author": "Christopher Nolan", "price": "649", "genre_title": "scifi"},
                {"title": "The Matrix", "title_ru": "Матрица", "author": "The Wachowskis", "price": "499", "genre_title": "scifi"},
                {"title": "Interstellar", "title_ru": "Интерстеллар", "author": "Christopher Nolan", "price": "699", "genre_title": "scifi"},
                {"title": "Star Wars: A New Hope", "title_ru": "Звёздные войны: Новая надежда", "author": "George Lucas", "price": "499", "genre_title": "scifi"},
                {"title": "The Empire Strikes Back", "title_ru": "Империя наносит ответный удар", "author": "Irvin Kershner", "price": "499", "genre_title": "scifi"},
            ]

            with database.atomic():
                Film.delete().execute()
                Film.insert_many(curated).execute()
        except Exception:
            pass
    finally:
        if not database.is_closed():
            database.close()
