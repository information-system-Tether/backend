from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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

        if "email" in err_type or "email" in msg.lower():
            translated = "Некорректный формат адреса электронной почты"
        elif err_type == "string_too_long":
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


