from contextlib import asynccontextmanager

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.config import get_settings
from auth.database import Base, engine, get_db
from auth.models import User
from auth.schemas import LoginRequest, TokenResponse, UserCreate, UserResponse
from auth.security import create_access_token, hash_password, verify_password


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Tether Auth Service",
    version="0.1.0",
    description="Регистрация, вход и проверка JWT-пользователя.",
    lifespan=lifespan,
)
bearer_scheme = HTTPBearer(scheme_name="JWT Bearer", description="Вставьте JWT-токен.")


@app.get(
    "/health",
    summary="Проверка доступности сервиса авторизации (не чекает био данные, это в diary)",
)
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="пароль сохраняется только в виде хэша от бикрипта.",
)
def register(user_data: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(login=user_data.login, email=user_data.email, password_hash=hash_password(user_data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sorry, this email is already registered")
    db.refresh(user)
    return user

@app.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="для получения токкена",
)
def login(user_data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.login == user_data.login))
    if user is None or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login or password, pls try again")
    return TokenResponse(access_token=create_access_token(user.id))

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token, check it and try again")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found, maybe u miss?")
    return user

@app.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Получить юзеар",
    description="Возвращает пользователя, которому принадлежит токен (нужна авторизация в bearer)",
)
def current_user(user: User = Depends(get_current_user)) -> User:
    return user
