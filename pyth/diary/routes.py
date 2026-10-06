from typing import Annotated
from fastapi import APIRouter, Depends, Header, Query, status
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

@router.get("/health/me", response_model=healresp, tags=["Профиль здоровья"], summary="Получить профиль здоровья")
def getheal(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> healresp:
    return healserv.getheal(db, idu)

@router.post("/health/me", response_model=healresp, status_code=status.HTTP_201_CREATED, tags=["Профиль здоровья"], summary="Создать профиль здоровья")
def createheal(data: healcreate, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> healresp:
    return healserv.createheal(db, idu, data)

@router.patch("/health/me", response_model=healresp, tags=["Профиль здоровья"], summary="Обновить профиль здоровья")
def updheal(data: healupd, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> healresp:
    return healserv.updheal(db, idu, data)

@router.delete("/health/me", status_code=status.HTTP_204_NO_CONTENT, tags=["Профиль здоровья"], summary="Удалить профиль здоровья")
def delheal(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> None:
    healserv.delheal(db, idu)

@router.get("/products/base", response_model=list[prodresp], tags=["Базовые продукты"], summary="Получить список базовых продуктов")
def listbase(db: Session = Depends(getdb)) -> list[baseprod]:
    return prodserv.listbase(db)

@router.post("/products/base/sync", status_code=status.HTTP_200_OK, tags=["Базовые продукты"], summary="Синхронизировать базовые продукты", dependencies=[Depends(veradm)])
def syncbase(prods: list[prodcreate], db: Session = Depends(getdb)) -> dict[str, int]:
    return {"synchronized": prodserv.syncbase(db, prods)}

@router.post("/products/me", response_model=prodresp, status_code=status.HTTP_201_CREATED, tags=["Пользовательские продукты"], summary="Добавить свой продукт")
def createpr(data: prodcreate, idu: int = Depends(getactualuid), db: Session = Depends(getdb), idemp: str | None = Header(None, alias="Idempotency-Key")) -> userprod:
    return prodserv.createpr(db, idu, data, idemp)

@router.get("/products/me", response_model=list[prodresp], tags=["Пользовательские продукты"], summary="Получить список своих продуктов")
def listpr(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> list[userprod]:
    return prodserv.listpr(db, idu)

@router.patch("/products/me/{idp}", response_model=prodresp, tags=["Пользовательские продукты"], summary="Обновить свой продукт")
def updatepr(idp: int, data: produpd, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> userprod:
    return prodserv.updatepr(db, idu, idp, data)

@router.delete("/products/me/{idp}", status_code=status.HTTP_204_NO_CONTENT, tags=["Пользовательские продукты"], summary="Удалить свой продукт")
def delpr(idp: int, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> None:
    prodserv.delpr(db, idu, idp)

@router.get("/favorites/me", response_model=list[favresp], response_model_exclude_none=True, tags=["Избранное"], summary="Получить список избранного")
def listfav(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> list[fav]:
    return prodserv.listfav(db, idu)

@router.post("/favorites/me", response_model=favresp, status_code=status.HTTP_201_CREATED, tags=["Избранное"], summary="Добавить в избранное")
def addfav(data: favcreate, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> fav:
    return prodserv.addfav(db, idu, data)

@router.delete("/favorites/me/{idf}", status_code=status.HTTP_204_NO_CONTENT, tags=["Избранное"], summary="Удалить из избранного")
def delfav(idf: int, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> None:
    prodserv.delfav(db, idu, idf)

@router.get("/sheets/me", tags=["Листы дневника"], response_model=list[sheetresp], response_model_exclude_none=True, summary="Получить историю листов дневника")
def listsheets(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> list[sheetresp]:
    return diaryserv.listsheets(db, idu)

@router.get("/sheets/me/dynamics", tags=["Аналитика"], response_model=dynresp, summary="Динамика потребления калорий за период дат")
def dynamics(
    d1: Annotated[str | None, Query(alias="start_date")] = None,
    d2: Annotated[str | None, Query(alias="end_date")] = None,
    idu: int = Depends(getactualuid),
    db: Session = Depends(getdb),
) -> dynresp:
    return diaryserv.getdyn(db, idu, d1=d1, d2=d2)

@router.get("/sheets/me/{dt}", tags=["Листы дневника"], response_model=sheetresp, response_model_exclude_none=True, summary="Получить лист дневника за дату")
def getsheet(dt: str, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> sheetresp:
    return diaryserv.getsheet(db, idu, dt)

@router.post("/sheets/me", tags=["Листы дневника"], response_model=sheetresp, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True, summary="Создать лист в дневнике")
def createsheet(data: sheetcreate, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> sheetresp:
    return diaryserv.createsheet(db, idu, data)

@router.patch("/sheets/me/{dt}", tags=["Листы дневника"], response_model=sheetresp, response_model_exclude_none=True, summary="Обновить лист дневника (записать вес)")
def updatesheet(dt: str, data: sheetupd, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> sheetresp:
    return diaryserv.updatesheet(db, idu, dt, data.weight)

@router.post("/sheets/me/{dt}/entries", tags=["Записи дневника"], response_model=entryresp, status_code=status.HTTP_201_CREATED, response_model_exclude_none=True, summary="Добавить запись в лист")
def createentry(dt: str, data: entrycreate, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> entryresp:
    return diaryserv.createentry(db, idu, dt, data)

@router.patch("/entries/me/{ide}", tags=["Записи дневника"], response_model=entryresp, response_model_exclude_none=True, summary="Обновить запись в дневнике")
def updateentry(ide: int, data: entryupd, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> entryresp:
    return diaryserv.updateentry(db, idu, ide, data)

@router.delete("/entries/me/{ide}", tags=["Записи дневника"], status_code=status.HTTP_204_NO_CONTENT, summary="Удалить запись из дневника")
def delentry(ide: int, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> None:
    diaryserv.delentry(db, idu, ide)

@router.get("/sync/me", tags=["Синхронизация?"], response_model=syncresp, summary="Выгрузить все данные пользователя")
def getsync(idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> syncresp:
    return diaryserv.getsync(db, idu)

@router.post("/sync/me", tags=["Синхронизация?"], status_code=status.HTTP_200_OK, summary="Синхронизировать данные пользователя")
def syncuser(data: syncdata, idu: int = Depends(getactualuid), db: Session = Depends(getdb)) -> dict[str, str]:
    diaryserv.syncuser(db, idu, data)
    return {"status": "synchronized"}

