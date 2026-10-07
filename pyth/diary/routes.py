from typing import Annotated
from fastapi import APIRouter, Body, Depends, Header, Path, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from diary.database import getdb
from diary.models import baseprod, fav, userprod
from diary.schemas import (
    daydyn, dynresp, entrycreate, entryresp, entryupd, favcreate, favresp,
    healcreate, healresp, healupd, prodcreate, prodresp, produpd,
    sheetcreate, sheetresp, sheetupd, syncdata, syncresp)
from diary.security import getactualuid, veradm
from diary.services import diaryserv, healserv, prodserv

router = APIRouter()

@router.get("/", include_in_schema=False)
def to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")

@router.get("/health/status", tags=["Система"], summary="Статус сервиса")
def stat() -> dict[str, str]:
    return {"status": "ok", "service": "diary"}

@router.get(
    "/health/me",
    response_model=healresp,
    tags=["Профиль здоровья"],
    summary="Получить профиль здоровья",
    description=(
        "Получение текущего профиля здоровья пользователя и рассчитанных норм.\n\n"
        "Возвращает введённые параметры тела, уровень активности (activity_level от 1 до 5), цель (target_goal от 1 до 4), а также рассчитанные математическим модулем персональные нормы:\n\n"
        "КБЖУ (диапазон калорий min_target_calories и max_target_calories, белки target_proteins, жиры target_fats, углеводы target_carbs), суточную норму воды target_water и целевые шаги target_steps."
    ),
)
def getheal(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> healresp:
    return healserv.getheal(db, idu)

@router.post(
    "/health/me",
    response_model=healresp,
    status_code=status.HTTP_201_CREATED,
    tags=["Профиль здоровья"],
    summary="Создать профиль здоровья",
    description=(
        "Создание профиля здоровья пользователя и автоматический расчёт персональных суточных норм.\n\n"
        "Константы уровня активности (activity_level):\n"
        "1 - сидячий образ жизни (малоподвижная работа, минимум нагрузок)\n"
        "2 - лёгкая активность (прогулки или лёгкие тренировки 1-3 раза в неделю)\n"
        "3 - умеренная активность (тренировки средней интенсивности 3-5 раз в неделю)\n"
        "4 - высокая активность (интенсивные тренировки 6-7 раз в неделю)\n"
        "5 - экстремальная активность (тяжёлый физический труд или ежедневный спорт)\n\n"
        "Константы целей (target_goal):\n"
        "1 - похудение (дефицит калорий для безопасного снижения веса)\n"
        "2 - набор массы (профицит калорий для роста мышечной массы)\n"
        "3 - рекомпозиция (сжигание жира с поддержанием мышечной массы)\n"
        "4 - удержание веса (баланс калорий для сохранения текущей формы)\n\n"
        "Все нормы КБЖУ (диапазон калорий, белки, жиры, углеводы), суточная норма воды и рекомендованное число шагов рассчитываются встроенным математическим модулем автоматически на основе параметров тела, уровня активности и цели.\n\n"
        "Если в поле target_steps передать 0, математический модуль рассчитает целевые шаги сам под выбранную активность и цель, а если указать число больше 0, сохранится персональная цель."
    ),
)
def createheal(
    data: Annotated[
        healcreate,
        Body(
            openapi_examples={
                "lose_weight": {
                    "summary": "Похудение (дефицит калорий)",
                    "value": {
                        "gender": "m",
                        "age": 25,
                        "weight": 85.0,
                        "height": 1.80,
                        "activity_level": 2,
                        "target_goal": 1,
                        "target_steps": 0,
                    },
                },
                "gain_muscle": {
                    "summary": "Набор массы (профицит калорий)",
                    "value": {
                        "gender": "m",
                        "age": 25,
                        "weight": 70.0,
                        "height": 1.78,
                        "activity_level": 3,
                        "target_goal": 2,
                        "target_steps": 0,
                    },
                },
                "maintain": {
                    "summary": "Удержание веса",
                    "value": {
                        "gender": "f",
                        "age": 28,
                        "weight": 60.0,
                        "height": 1.68,
                        "activity_level": 2,
                        "target_goal": 4,
                        "target_steps": 0,
                    },
                },
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> healresp:
    return healserv.createheal(db, idu, data)

@router.patch(
    "/health/me",
    response_model=healresp,
    tags=["Профиль здоровья"],
    summary="Обновить профиль здоровья",
    description=(
        "Частичное обновление параметров профиля здоровья пользователя.\n\n"
        "При изменении веса, роста, возраста, пола, уровня активности или цели математический модуль автоматически пересчитывает все нормы КБЖУ, норму воды и количество шагов под новые параметры тела.\n\n"
        "Константы уровня активности (activity_level):\n"
        "1 - сидячий образ жизни (малоподвижная работа, минимум нагрузок)\n"
        "2 - лёгкая активность (прогулки или лёгкие тренировки 1-3 раза в неделю)\n"
        "3 - умеренная активность (тренировки средней интенсивности 3-5 раз в неделю)\n"
        "4 - высокая активность (интенсивные тренировки 6-7 раз в неделю)\n"
        "5 - экстремальная активность (тяжёлый физический труд или ежедневный спорт)\n\n"
        "Константы целей (target_goal):\n"
        "1 - похудение (дефицит калорий для безопасного снижения веса)\n"
        "2 - набор массы (профицит калорий для роста мышечной массы)\n"
        "3 - рекомпозиция (сжигание жира с поддержанием мышечной массы)\n"
        "4 - удержание веса (баланс калорий для сохранения текущей формы)\n\n"
        "Все нормы КБЖУ, вода и шаги рассчитываются математическим модулем автоматически.\n\n"
        "Если в поле target_steps передать 0, математический модуль пересчитает шаги сам под новую активность и цель, а если передать значение больше 0, сохранится ваша персональная цель."
    ),
)
def updheal(
    data: Annotated[
        healupd,
        Body(
            openapi_examples={
                "update_weight": {
                    "summary": "Обновление веса (пересчёт КБЖУ и воды)",
                    "value": {
                        "weight": 83.5,
                    },
                },
                "change_goal": {
                    "summary": "Смена цели на удержание веса",
                    "value": {
                        "target_goal": 4,
                    },
                },
                "change_activity": {
                    "summary": "Изменение активности и цели",
                    "value": {
                        "activity_level": 3,
                        "target_goal": 3,
                    },
                },
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> healresp:
    return healserv.updheal(db, idu, data)

@router.delete(
    "/health/me",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Профиль здоровья"],
    summary="Удалить профиль здоровья",
    description="Удаление профиля здоровья текущего пользователя и сброс рассчитанных норм.",
)
def delheal(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> None:
    healserv.delheal(db, idu)

@router.get("/products/base", response_model=list[prodresp], tags=["Базовые продукты"], summary="Получить список базовых продуктов")
def listbase(db: Session = Depends(getdb)) -> list[baseprod]:
    return prodserv.listbase(db)

@router.post("/products/base/sync", status_code=status.HTTP_200_OK, tags=["Базовые продукты"], summary="Синхронизировать базовые продукты", dependencies=[Depends(veradm)])
def syncbase(prods: list[prodcreate], db: Session = Depends(getdb)) -> dict[str, int]:
    return {"synchronized": prodserv.syncbase(db, prods)}

@router.post("/products/me", response_model=prodresp, status_code=status.HTTP_201_CREATED, tags=["Пользовательские продукты"], summary="Добавить свой продукт")
def createpr(
    data: Annotated[
        prodcreate,
        Body(
            openapi_examples={
                "example": {
                    "summary": "Филе минтая в панировке Экспродов",
                    "value": {
                        "name": "Филе минтая в панировке Экспродов",
                        "description": "Рыбные котлетки в кляре, ",
                        "product_type": "meatfish",
                        "calories": 130,
                        "fats": 15,
                        "proteins": 6.5,
                        "carbs": 5,
                    },
                }
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> userprod:
    return prodserv.createpr(db, idu, data)

@router.get("/products/me", response_model=list[prodresp], tags=["Пользовательские продукты"], summary="Получить список своих продуктов")
def listpr(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> list[userprod]:
    return prodserv.listpr(db, idu)

@router.patch("/products/me/{idp}", response_model=prodresp, tags=["Пользовательские продукты"], summary="Обновить свой продукт")
def updatepr(
    idp: Annotated[int, Path(description="ID пользовательского продукта", example=1)],
    data: Annotated[
        produpd,
        Body(
            openapi_examples={
                "example": {
                    "summary": "Обновление параметров продукта",
                    "value": {
                        "name": "Филе минтая в панировке (обновлённый состав)",
                        "calories": 140,
                        "fats": 16,
                        "proteins": 7,
                        "carbs": 6,
                    },
                }
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> userprod:
    return prodserv.updatepr(db, idu, idp, data)

@router.delete("/products/me/{idp}", status_code=status.HTTP_204_NO_CONTENT, tags=["Пользовательские продукты"], summary="Удалить свой продукт")
def delpr(
    idp: Annotated[int, Path(description="ID пользовательского продукта", example=1)],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> None:
    prodserv.delpr(db, idu, idp)

@router.get("/favorites/me", response_model=list[favresp], response_model_exclude_none=True, tags=["Избранное"], summary="Получить список избранного")
def listfav(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> list[fav]:
    return prodserv.listfav(db, idu)

@router.post(
    "/favorites/me",
    response_model=favresp,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    tags=["Избранное"],
    summary="Добавить в избранное",
    description=(
        "Добавление продукта в список избранного пользователя.\n\n"
        "Необходимо указать ровно один идентификатор продукта:\n"
        "base_product_id - для системного продукта из каталога базовых продуктов\n"
        "user_product_id - для собственного (пользовательского) ранее созданного продукта\n\n"
        "Используйте подходящий шаблон в выпадающем списке Examples."
    ),
)
def addfav(
    data: Annotated[
        favcreate,
        Body(
            openapi_examples={
                "base_catalog": {
                    "summary": "Базовый продукт из каталога (base_product_id)",
                    "description": "Добавление в избранное системного продукта из каталога базовых продуктов",
                    "value": {
                        "base_product_id": 1,
                    },
                },
                "user_catalog": {
                    "summary": "Свой продукт (user_product_id)",
                    "description": "Добавление в избранное собственного ранее созданного продукта",
                    "value": {
                        "user_product_id": 1,
                    },
                },
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> fav:
    return prodserv.addfav(db, idu, data)

@router.delete("/favorites/me/{idf}", status_code=status.HTTP_204_NO_CONTENT, tags=["Избранное"], summary="Удалить из избранного")
def delfav(
    idf: Annotated[int, Path(description="ID записи в избранном", example=1)],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> None:
    prodserv.delfav(db, idu, idf)

@router.get(
    "/sheets/me",
    tags=["Листы дневника"],
    response_model=list[sheetresp],
    response_model_exclude_none=True,
    summary="Получить историю листов дневника",
    description="Возвращает историю дневниковых листов пользователя в порядке убывания даты со списком всех приёмов пищи и суммарными показателями КБЖУ и воды за каждый день.",
)
def listsheets(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> list[sheetresp]:
    return diaryserv.listsheets(db, idu)

@router.get(
    "/sheets/me/dynamics",
    tags=["Аналитика"],
    response_model=dynresp,
    summary="Динамика потребления калорий и веса за период дат",
    description=(
        "Возвращает аналитику питания и веса за указанный период (start_date, end_date).\n\n"
        "days_count: количество дней с созданными записями за этот период.\n"
        "average_weight: средний вес пользователя за период.\n"
        "average_calories: среднее суточное потребление калорий.\n"
        "days: массив дней со значением weight (вес) и суммарными КБЖУ дня (используется для построения графиков)."
    ),
)
def dynamics(
    d1: Annotated[str | None, Query(alias="start_date")] = None,
    d2: Annotated[str | None, Query(alias="end_date")] = None,
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> dynresp:
    return diaryserv.getdyn(db, idu, d1=d1, d2=d2)

@router.get("/sheets/me/{dt}", tags=["Листы дневника"], response_model=sheetresp, response_model_exclude_none=True, summary="Получить лист дневника за дату")
def getsheet(
    dt: Annotated[str, Path(description="Дата листа дневника (YYYY-MM-DD, например 2026-10-07, или 'today')", example="today")],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> sheetresp:
    return diaryserv.getsheet(db, idu, dt)

@router.post(
    "/sheets/me",
    tags=["Листы дневника"],
    response_model=sheetresp,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    summary="Создать лист в дневнике",
    description="Создание дневникового листа за указанную дату (или 'today').",
)
def createsheet(
    data: Annotated[
        sheetcreate,
        Body(
            openapi_examples={
                "today": {
                    "summary": "Лист за сегодня с весом",
                    "value": {
                        "sheet_date": "today",
                        "weight": 80.0,
                    },
                },
                "specific_date": {
                    "summary": "Лист за конкретную дату",
                    "value": {
                        "sheet_date": "2026-10-07",
                        "weight": 80.0,
                    },
                },
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> sheetresp:
    return diaryserv.createsheet(db, idu, data)

@router.patch("/sheets/me/{dt}", tags=["Листы дневника"], response_model=sheetresp, response_model_exclude_none=True, summary="Обновить лист дневника (записать вес)")
def updatesheet(
    dt: Annotated[str, Path(description="Дата листа дневника (YYYY-MM-DD, например 2026-10-07, или 'today')", example="today")],
    data: Annotated[
        sheetupd,
        Body(
            openapi_examples={
                "example": {
                    "summary": "Запись веса за день",
                    "value": {
                        "weight": 79.5,
                    },
                }
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> sheetresp:
    return diaryserv.updatesheet(db, idu, dt, data.weight)

@router.delete(
    "/sheets/me/{dt}",
    tags=["Листы дневника"],
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить лист дневника за дату",
    description="Удаление дневникового листа за указанную дату. При удалении листа автоматически удаляются все связанные с ним записи приёмов пищи.",
)
def delsheet(
    dt: Annotated[str, Path(description="Дата листа дневника (YYYY-MM-DD или 'today')", example="today")],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> None:
    diaryserv.delsheet(db, idu, dt)

@router.post(
    "/sheets/me/{dt}/entries",
    tags=["Записи дневника"],
    response_model=entryresp,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    summary="Добавить запись в лист",
    description=(
        "Добавление съеденного продукта или блюда в дневник за дату {dt}.\n\n"
        "Шаблон с name, description, product_type, calories, fats, proteins, carbs использовать ТОЛЬКО ЕСЛИ НЕ ЗАТРАГИВАЕТСЯ base_product_id и user_product_id, т.е. если они пусты/null (разовый ручной ввод продукта в дневник).\n\n"
        "Если запись создаётся на основе продукта из каталога или своих продуктов, изначально все эти поля должны быть пустыми (null), и тогда указывается ТОЛЬКО base_product_id (или user_product_id) и quantity_grams (граммы) - итоговые КБЖУ рассчитаются автоматически под указанный вес порции!\n\n"
        "Для второго и третьего случая использовать два иных примера шаблонов JSON."
    ),
)
def createentry(
    dt: Annotated[str, Path(description="Дата листа дневника (YYYY-MM-DD, например 2026-10-07, или 'today')", example="today")],
    data: Annotated[
        entrycreate,
        Body(
            openapi_examples={
                "manual": {
                    "summary": "Ручной ввод",
                    "description": "Использовать ТОЛЬКО если base_product_id и user_product_id равны null или пусты, т.е. единоразовая запись",
                    "value": {
                        "name": "Филе минтая в панировке Экспродов",
                        "description": "Рыбные котлетки в кляре, ",
                        "product_type": "meatfish",
                        "calories": 130,
                        "fats": 16,
                        "proteins": 6.5,
                        "carbs": 5,
                        "quantity_grams": 100,
                    },
                },
                "base_catalog": {
                    "summary": "Базовый продукт из каталога (base_product_id)",
                    "description": "Использование готового продукта системой. КБЖУ рассчитываются автоматически под вес порции",
                    "value": {
                        "base_product_id": 1,
                        "quantity_grams": 100,
                    },
                },
                "user_catalog": {
                    "summary": "Пользовательский продукт из каталога (user_product_id)",
                    "description": "Использование ранее созданного своего продукта. КБЖУ рассчитываются автоматически под вес порции",
                    "value": {
                        "user_product_id": 1,
                        "quantity_grams": 100,
                    },
                },
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> entryresp:
    return diaryserv.createentry(db, idu, dt, data)

@router.patch(
    "/entries/me/{ide}",
    tags=["Записи дневника"],
    response_model=entryresp,
    response_model_exclude_none=True,
    summary="Обновить запись в дневнике",
    description=(
        "Обновление записи дневника по её ID.\n\n"
        "Для продуктов из каталога (базовых или своих) достаточно передать новое значение quantity_grams - КБЖУ пересчитаются автоматически.\n\n"
        "Для разовой ручной записи можно обновить название, граммы и КБЖУ."
    ),
)
def updateentry(
    ide: Annotated[int, Path(description="ID записи дневника", example=1)],
    data: Annotated[
        entryupd,
        Body(
            openapi_examples={
                "change_quantity": {
                    "summary": "Изменение веса порции (для продукта из каталога или своего)",
                    "description": "Автоматически пересчитает КБЖУ порции на основе продукта",
                    "value": {
                        "quantity_grams": 150,
                    },
                },
                "update_manual": {
                    "summary": "Редактирование ручной записи",
                    "description": "Изменение названия и значений КБЖУ для произвольной записи",
                    "value": {
                        "title": "Филе минтая в кляре",
                        "quantity_grams": 150,
                        "calories": 195,
                        "proteins": 9.75,
                        "fats": 24,
                        "carbs": 7.5,
                    },
                },
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> entryresp:
    return diaryserv.updateentry(db, idu, ide, data)

@router.delete("/entries/me/{ide}", tags=["Записи дневника"], status_code=status.HTTP_204_NO_CONTENT, summary="Удалить запись из дневника")
def delentry(
    ide: Annotated[int, Path(description="ID записи дневника", example=1)],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> None:
    diaryserv.delentry(db, idu, ide)

@router.get("/sync/me", tags=["Синхронизация?"], response_model=syncresp, summary="Выгрузить все данные пользователя")
def getsync(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> syncresp:
    return diaryserv.getsync(db, idu)

@router.post(
    "/sync/me",
    tags=["Синхронизация?"],
    status_code=status.HTTP_200_OK,
    summary="Синхронизировать данные пользователя",
    description="Синхронизация данных профиля здоровья и пользовательских сущностей.",
)
def syncuser(
    data: Annotated[
        syncdata,
        Body(
            openapi_examples={
                "health_sync": {
                    "summary": "Синхронизация профиля здоровья",
                    "value": {
                        "health": {
                            "gender": "m",
                            "age": 25,
                            "weight": 80,
                            "height": 1.8,
                            "activity_level": 1,
                            "target_goal": 1,
                            "target_steps": 10000,
                        }
                    },
                }
            }
        ),
    ],
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> dict[str, str]:
    diaryserv.syncuser(db, idu, data)
    return {"status": "synchronized"}

