from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from database import User, database
from schemas import UserCreate, UserResponse, Token, UserLogin
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

@router.get("/users", response_model=list[UserResponse])
async def read_users(current_user: User = Depends(get_current_active_user)):
    """Получить список всех пользователей (только для аутентифицированных пользователей)"""
    users = User.select()
    return [UserResponse.model_validate(user, from_attributes=True) for user in users]
