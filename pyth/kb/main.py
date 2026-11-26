from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from kb.database import Base, SessionLocal, engine
from kb.seed_kb import seedkb
from kb.routes import router

@asynccontextmanager
async def longlive(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seedkb(db)
    yield

app = FastAPI(
    title="Tether Knowledge Base",
    version="1.0",
    description="Микросервис базы знаний: часто задаваемые вопросы о питании, калорийности и нутриентах с поиском по ключевым словам.",
    lifespan=longlive)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Total-Count",
        "X-Page",
        "X-Page-Size",
        "X-Total-Pages",
        "X-Has-Next",
        "X-Has-Prev",
    ],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        err_type = err.get("type", "")
        msg = err.get("msg", "")
        ctx = err.get("ctx", {})
        loc = list(err.get("loc", []))
        field_name = str(loc[-1]) if loc else "поле"

        if err_type == "value_error" and any(ord(c) > 127 for c in msg):
            custom_msg = msg.replace("Value error, ", "")
            errors.append({"loc": loc, "msg": custom_msg, "type": err_type})
            continue

        if err_type == "string_too_long":
            max_len = ctx.get("max_length")
            translated = f"Длина поля не должна превышать {max_len} символов"
        elif err_type == "string_too_short":
            min_len = ctx.get("min_length")
            translated = f"Длина поля должна быть не менее {min_len} символов"
        elif err_type == "missing":
            translated = "Обязательное поле отсутствует"
        else:
            translated = msg

        errors.append({"loc": loc, "msg": translated, "type": err_type})
    return JSONResponse(status_code=422, content={"detail": errors})

app.include_router(router)
