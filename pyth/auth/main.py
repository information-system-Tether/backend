from contextlib import asynccontextmanager
from fastapi import FastAPI
from auth.database import Base, engine
from auth.routes import router

@asynccontextmanager
async def longlive(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Tether Auth Service",
    version="2.2",
    description="Регистрация, вход, выход (отзыв токена) и проверка профиля пользователя.",
    lifespan=longlive)
app.include_router(router)

