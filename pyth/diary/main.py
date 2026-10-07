from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from diary.database import Base, SessionLocal, addcols, engine
from diary.baseproducts import seedbase
from diary.routes import router

@asynccontextmanager
async def longlive(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    addcols()
    with SessionLocal() as db:
        seedbase(db)
    yield

app = FastAPI(
    title="Tether Diary Service",
    version="2.2",
    description="Микросервис дневника питания, аналитики нутриентов и профиля здоровья.",
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

        if err_type == "greater_than":
            limit = ctx.get("gt", 0)
            if field_name == "quantity_grams":
                translated = "Количество продукта в граммах должно быть строго больше 0 (не может быть равным 0 или отрицательным)"
            elif field_name in ("weight", "height"):
                translated = f"Значение поля {field_name} должно быть строго больше {limit} (не может быть отрицательным или нулевым)"
            elif field_name in ("base_product_id", "user_product_id", "id", "ide", "idp", "idf"):
                translated = "Идентификатор должен быть положительным целым числом"
            else:
                translated = f"Значение поля должно быть строго больше {limit} (не может быть отрицательным или нулевым)"
        elif err_type == "greater_than_equal":
            limit = ctx.get("ge", 0)
            if limit == 0:
                translated = "Значение поля должно быть не менее 0 (не может быть отрицательным)"
            elif field_name == "age":
                translated = f"Возраст должен быть не менее {limit} полных лет"
            else:
                translated = f"Значение поля должно быть не менее {limit}"
        elif err_type == "less_than_equal":
            limit = ctx.get("le")
            if field_name == "age":
                translated = f"Возраст должен быть не более {limit} лет"
            elif field_name == "weight":
                translated = f"Вес должен быть не более {limit} кг"
            elif field_name == "height":
                translated = f"Рост должен быть не более {limit} м"
            else:
                translated = f"Значение поля должно быть не более {limit}"
        elif err_type == "string_too_long":
            max_len = ctx.get("max_length")
            translated = f"Длина поля не должна превышать {max_len} символов"
        elif err_type == "string_too_short":
            min_len = ctx.get("min_length")
            translated = f"Длина поля должна быть не менее {min_len} символов"
        elif err_type in ("decimal_parsing", "float_parsing", "int_parsing", "int_type", "float_type", "decimal_type", "int_from_number"):
            translated = "Поле должно содержать только числовое значение (цифры), буквы и специальные символы не допускаются"
        elif err_type == "missing":
            translated = "Обязательное поле отсутствует"
        elif err_type == "enum":
            expected = ctx.get("expected")
            translated = f"Недопустимое значение. Допустимые варианты: {expected}"
        elif "date" in err_type:
            translated = "Неверный формат даты. Требуется использовать формат YYYY-MM-DD или 'today'"
        else:
            translated = msg

        errors.append({"loc": loc, "msg": translated, "type": err_type})
    return JSONResponse(status_code=422, content={"detail": errors})

app.include_router(router)

