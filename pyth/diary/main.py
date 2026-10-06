from contextlib import asynccontextmanager
from fastapi import FastAPI
from diary.database import Base, engine
from diary.routes import router

@asynccontextmanager
async def longlive(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Tether Diary Service",
    version="2.2",
    description="Микросервис дневника питания, аналитики нутриентов и профиля здоровья.",
    lifespan=longlive)
app.include_router(router)

