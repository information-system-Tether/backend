from __future__ import annotations
from typing import Annotated
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from kb.database import getdb
from kb.schemas import kbcreate, kbpaginated, kbresp, kbupd
from kb.security import veradm
from kb.services import kbserv

router = APIRouter()

def _resolve_pagination(
    page: int | None,
    page_size: int | None,
    limit: int | None,
    offset: int,
) -> tuple[int, int | None, int]:
    if page is not None:
        eff_size = page_size if page_size is not None else 20
        calc_offset = (page - 1) * eff_size
        calc_limit = eff_size
    elif limit is not None:
        eff_size = limit
        calc_offset = offset
        calc_limit = limit
    elif page_size is not None:
        eff_size = page_size
        calc_offset = 0
        calc_limit = page_size
    else:
        eff_size = 20
        calc_offset = offset
        calc_limit = None
    return calc_offset, calc_limit, eff_size

def _set_pagination_headers(
    response: Response,
    total: int,
    calc_offset: int,
    calc_limit: int | None,
    eff_size: int,
    items_count: int,
) -> None:
    eff_page = (calc_offset // eff_size) + 1 if eff_size > 0 else 1
    total_pages = (total + eff_size - 1) // eff_size if (total > 0 and eff_size > 0) else 1
    has_next = (eff_page < total_pages) if calc_limit is not None else False
    has_prev = (eff_page > 1) if calc_limit is not None else False

    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(eff_page)
    response.headers["X-Page-Size"] = str(calc_limit if calc_limit is not None else items_count)
    response.headers["X-Total-Pages"] = str(total_pages)
    response.headers["X-Has-Next"] = str(has_next).lower()
    response.headers["X-Has-Prev"] = str(has_prev).lower()

@router.get("/", include_in_schema=False)
def to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")

@router.get("/health/status", tags=["Система"], summary="Статус сервиса")
def stat() -> dict[str, str]:
    return {"status": "ok", "service": "kb"}

@router.get(
    "/kb",
    response_model=list[kbresp],
    tags=["База знаний"],
    summary="Получить статьи базы знаний (с фильтрацией и пагинацией)",
    description=(
        "Возвращает список статей. Поддерживает выбор по тематическому блоку, категории, "
        "поиск по ключевым словам и пагинацию.\n\n"
        "Пагинация поддерживается как через `page`/`page_size`, так и через `limit`/`offset`.\n"
        "Метаданные пагинации возвращаются в заголовках ответа: `X-Total-Count`, `X-Page`, `X-Page-Size`, `X-Total-Pages`, `X-Has-Next`, `X-Has-Prev`."
    ),
)
def listarticles(
    response: Response,
    category: Annotated[str | None, Query(description="Фильтр по категории (general, calories, nutrients, methods, standards, hydration)")] = None,
    block: Annotated[str | None, Query(description="Фильтр по тематическому блоку")] = None,
    q: Annotated[str | None, Query(description="Поиск по ключевым словам (внутри блока/категории или по всей базе)")] = None,
    page: Annotated[int | None, Query(description="Номер страницы (начиная с 1)", ge=1)] = None,
    page_size: Annotated[int | None, Query(description="Количество записей на страницу (по умолчанию 20)", ge=1, le=100)] = None,
    limit: Annotated[int | None, Query(description="Лимит записей (альтернатива page_size)", ge=1, le=1000)] = None,
    offset: Annotated[int, Query(description="Смещение записей (альтернатива page)", ge=0)] = 0,
    db: Session = Depends(getdb),
) -> list[kbresp]:
    calc_offset, calc_limit, eff_size = _resolve_pagination(page, page_size, limit, offset)
    items, total = kbserv.listarticles(db, category=category, block=block, q=q, offset=calc_offset, limit=calc_limit)
    _set_pagination_headers(response, total, calc_offset, calc_limit, eff_size, len(items))
    return items

@router.get(
    "/kb/paginated",
    response_model=kbpaginated,
    tags=["База знаний"],
    summary="Получить статьи базы знаний в виде структуры с пагинацией (JSON)",
    description=(
        "Возвращает JSON-объект с массивом `items` и метаданными пагинации (`total`, `page`, `page_size`, `total_pages`, `has_next`, `has_prev`).\n\n"
        "Удобно для клиентов, которым предпочтительнее структурированный ответ в теле, чем чтение заголовков."
    ),
)
def listarticles_paginated(
    category: Annotated[str | None, Query(description="Фильтр по категории")] = None,
    block: Annotated[str | None, Query(description="Фильтр по тематическому блоку")] = None,
    q: Annotated[str | None, Query(description="Поиск по ключевым словам")] = None,
    page: Annotated[int, Query(description="Номер страницы (начиная с 1)", ge=1)] = 1,
    page_size: Annotated[int, Query(description="Количество записей на страницу", ge=1, le=100)] = 20,
    db: Session = Depends(getdb),
) -> kbpaginated:
    calc_offset = (page - 1) * page_size
    items, total = kbserv.listarticles(db, category=category, block=block, q=q, offset=calc_offset, limit=page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return kbpaginated(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1,
    )

@router.get(
    "/kb/blocks",
    response_model=list[str],
    tags=["База знаний"],
    summary="Получить список всех тематических блоков",
    description="Возвращает список названий всех тематических блоков для группировки и навигации.",
)
def listblocks(
    db: Session = Depends(getdb),
) -> list[str]:
    return kbserv.listblocks(db)

@router.get(
    "/kb/search",
    response_model=list[kbresp],
    tags=["База знаний"],
    summary="Поиск по базе знаний",
    description=(
        "Полнотекстовый поиск по вопросам, ответам, тегам и блокам с поддержкой пагинации.\n\n"
        "Поиск выполняется по всем переданным словам (AND-логика): статья попадает в результат, "
        "только если каждое слово встречается хотя бы в одном из полей.\n\n"
        "Пример: `q=калорийность упаковка` найдёт статьи, содержащие оба слова."
    ),
)
def search(
    response: Response,
    q: Annotated[str, Query(description="Поисковый запрос (ключевые слова через пробел)", min_length=1)],
    category: Annotated[str | None, Query(description="Фильтр по категории")] = None,
    block: Annotated[str | None, Query(description="Фильтр по тематическому блоку")] = None,
    page: Annotated[int | None, Query(description="Номер страницы (начиная с 1)", ge=1)] = None,
    page_size: Annotated[int | None, Query(description="Количество записей на страницу", ge=1, le=100)] = None,
    limit: Annotated[int | None, Query(description="Лимит записей (альтернатива page_size)", ge=1, le=1000)] = None,
    offset: Annotated[int, Query(description="Смещение записей", ge=0)] = 0,
    db: Session = Depends(getdb),
) -> list[kbresp]:
    calc_offset, calc_limit, eff_size = _resolve_pagination(page, page_size, limit, offset)
    items, total = kbserv.search(db, q=q, category=category, block=block, offset=calc_offset, limit=calc_limit)
    _set_pagination_headers(response, total, calc_offset, calc_limit, eff_size, len(items))
    return items

@router.get(
    "/kb/{aid}",
    response_model=kbresp,
    tags=["База знаний"],
    summary="Получить статью по ID",
)
def getarticle(
    aid: Annotated[int, Path(description="ID статьи базы знаний", examples=[1])],
    db: Session = Depends(getdb),
) -> kbresp:
    return kbserv.getarticle(db, aid)

@router.post(
    "/kb",
    response_model=kbresp,
    status_code=status.HTTP_201_CREATED,
    tags=["База знаний"],
    summary="Создать статью",
    description="Добавление новой статьи в базу знаний. Требуется административный ключ.",
    dependencies=[Depends(veradm)],
)
def createarticle(
    data: Annotated[
        kbcreate,
        Body(
            openapi_examples={
                "calories_packaging": {
                    "summary": "Калорийность на упаковку",
                    "value": {
                        "question": "В каких странах калорийность указывается для всей упаковки, а не для 100 г?",
                        "answer": "Такое распространено в США (требование FDA – указывать Nutrition Facts на порцию, размер которой определяет производитель) и в Южной Корее (стандарт MFDS). В ЕС и России КБЖУ указываются на 100 г/100 мл.",
                        "category": "standards",
                        "block": "Стандарты, маркировка и законы",
                        "tags": "калорийность,упаковка,FDA,MFDS,США,Корея,стандарт",
                    },
                },
                "inedible_parts": {
                    "summary": "Продукт с несъедобной частью",
                    "value": {
                        "question": "Как правильно рассчитать калорийность продукта, содержащего несъедобную часть?",
                        "answer": "Взвесьте продукт до употребления и после (кости, кожура, скорлупа). Разница – съедобная масса. КБЖУ рассчитывайте только от съедобной части.",
                        "category": "methods",
                        "block": "Методы взвешивания, расчёта и учёта",
                        "tags": "калорийность,расчёт,несъедобная часть,кости,кожура",
                    },
                },
            }
        ),
    ],
    db: Session = Depends(getdb),
) -> kbresp:
    return kbserv.createarticle(db, data)

@router.patch(
    "/kb/{aid}",
    response_model=kbresp,
    tags=["База знаний"],
    summary="Обновить статью",
    description="Частичное обновление статьи базы знаний. Требуется административный ключ.",
    dependencies=[Depends(veradm)],
)
def updatearticle(
    aid: Annotated[int, Path(description="ID статьи базы знаний", examples=[1])],
    data: Annotated[
        kbupd,
        Body(
            openapi_examples={
                "update_answer": {
                    "summary": "Обновление ответа",
                    "value": {
                        "answer": "Обновлённый текст ответа с дополнительными деталями.",
                    },
                },
            }
        ),
    ],
    db: Session = Depends(getdb),
) -> kbresp:
    return kbserv.updatearticle(db, aid, data)

@router.delete(
    "/kb/{aid}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["База знаний"],
    summary="Удалить статью",
    description="Удаление статьи из базы знаний. Требуется административный ключ.",
    dependencies=[Depends(veradm)],
)
def delarticle(
    aid: Annotated[int, Path(description="ID статьи базы знаний", examples=[1])],
    db: Session = Depends(getdb),
) -> None:
    kbserv.delarticle(db, aid)
