from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from database import User, Bookmark, CartItem, database, Film
from schemas import UserCreate, UserResponse, Token, UserLogin, AvatarUpdate
from auth import (
    authenticate_user, 
    create_access_token, 
    get_password_hash, 
    get_current_active_user
)
from config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Регистрация нового пользователя"""
    try:
        # Проверяем, существует ли пользователь с таким username
        existing_user = User.get_or_none(User.username == user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже существует"
            )
        
        # Проверяем, существует ли пользователь с таким email
        existing_email = User.get_or_none(User.email == user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
        
        # Создаем нового пользователя в транзакции
        hashed_password = get_password_hash(user_data.password)
        with database.atomic():
            user = User.create(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password
            )
            # Повторно читаем из БД, чтобы получить значения полей по умолчанию
            user = User.get(User.id == user.id)
        
        return UserResponse.model_validate(user, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Вход в систему"""
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Получить информацию о текущем пользователе"""
    return UserResponse.model_validate(current_user, from_attributes=True)

@router.put("/me/avatar", response_model=UserResponse)
async def update_avatar(payload: AvatarUpdate, current_user: User = Depends(get_current_active_user)):
    """Обновить аватар текущего пользователя (base64)"""
    # Небольшая валидация: ограничим размер строки, чтобы не переполнять БД случайно
    if not payload.avatar_base64 or len(payload.avatar_base64) > 5_000_000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Некорректный размер изображения")
    current_user.avatar_base64 = payload.avatar_base64
    current_user.save()
    return UserResponse.model_validate(current_user, from_attributes=True)

# --- Закладки ---
from pydantic import BaseModel
from typing import List

class BookmarkCreate(BaseModel):
    movie_id: str
    title: str
    author: str | None = None
    price: str | None = None

class BookmarkResponse(BaseModel):
    id: int
    movie_id: str
    title: str
    author: str | None = None
    price: str | None = None

    class Config:
        from_attributes = True

@router.get("/bookmarks", response_model=List[BookmarkResponse])
async def list_bookmarks(current_user: User = Depends(get_current_active_user)):
    items = Bookmark.select().where(Bookmark.user == current_user)
    return [BookmarkResponse.model_validate(item, from_attributes=True) for item in items]

@router.post("/bookmarks", response_model=BookmarkResponse, status_code=status.HTTP_201_CREATED)
async def add_bookmark(payload: BookmarkCreate, current_user: User = Depends(get_current_active_user)):
    try:
        with database.atomic():
            item, created = Bookmark.get_or_create(
                user=current_user,
                movie_id=payload.movie_id,
                defaults={
                    'title': payload.title,
                    'author': payload.author,
                    'price': payload.price,
                }
            )
            if not created:
                # обновим данные, если менялись
                item.title = payload.title
                item.author = payload.author
                item.price = payload.price
                item.save()
        return BookmarkResponse.model_validate(item, from_attributes=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось добавить закладку: {e}")

@router.delete("/bookmarks/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(movie_id: str, current_user: User = Depends(get_current_active_user)):
    deleted = Bookmark.delete().where((Bookmark.user == current_user) & (Bookmark.movie_id == movie_id)).execute()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Закладка не найдена")
    return

# --- Корзина ---
class CartItemCreate(BaseModel):
    movie_id: str
    title: str
    author: str | None = None
    price: str | None = None

class CartItemResponse(BaseModel):
    id: int
    movie_id: str
    title: str
    author: str | None = None
    price: str | None = None

    class Config:
        from_attributes = True

@router.get("/cart", response_model=List[CartItemResponse])
async def list_cart(current_user: User = Depends(get_current_active_user)):
    items = CartItem.select().where(CartItem.user == current_user)
    return [CartItemResponse.model_validate(item, from_attributes=True) for item in items]

@router.post("/cart", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(payload: CartItemCreate, current_user: User = Depends(get_current_active_user)):
    try:
        with database.atomic():
            item, created = CartItem.get_or_create(
                user=current_user,
                movie_id=payload.movie_id,
                defaults={
                    'title': payload.title,
                    'author': payload.author,
                    'price': payload.price,
                }
            )
            if not created:
                item.title = payload.title
                item.author = payload.author
                item.price = payload.price
                item.save()
        return CartItemResponse.model_validate(item, from_attributes=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Не удалось добавить в корзину: {e}")

@router.delete("/cart/{movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(movie_id: str, current_user: User = Depends(get_current_active_user)):
    deleted = CartItem.delete().where((CartItem.user == current_user) & (CartItem.movie_id == movie_id)).execute()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")
    return

# --- Смена пароля ---
from schemas import PasswordChange
from auth import verify_password

@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(payload: PasswordChange, current_user: User = Depends(get_current_active_user)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Текущий пароль неверен")
    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Новый пароль слишком короткий")
    current_user.hashed_password = get_password_hash(payload.new_password)
    current_user.save()
    return

# --- Фильмы по жанрам ---
class FilmResponse(BaseModel):
    flim_id: int
    title: str
    title_ru: str | None = None
    author: str | None = None
    price: str | None = None
    genre_title: str
    movie_base64: str | None = None

    class Config:
        from_attributes = True

@router.get("/genres/{genre}/films", response_model=List[FilmResponse])
async def get_films_by_genre(genre: str):
    # Приводим жанр к нижнему регистру для соответствия данным
    g = genre.strip().lower()
    q = Film.select().where(Film.genre_title == g)
    return [FilmResponse.model_validate(f, from_attributes=True) for f in q]
