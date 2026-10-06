from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from auth.database import getdb
from auth.lim import limiter
from auth.models import usr
from auth.schemas import loginreq, msgresp, tokenresp, useradd, useresp
from auth.service import authserv

router = APIRouter()
bearer_scheme = HTTPBearer(scheme_name="JWT Bearer", description="Bearer JWT-токен")
authlim = limiter(limit=10, window=60)

@router.get("/", include_in_schema=False)
def to_docs() -> RedirectResponse:
    return RedirectResponse(url="/docs")

def getactualuser(cred: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(getdb)) -> usr:
    return authserv.getuser(db, cred.credentials)

@router.get("/health", tags=["Система"], summary="Проверка доступности сервиса авторизации")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "auth"}

@router.post("/auth/register", response_model=useresp, status_code=status.HTTP_201_CREATED, tags=["Аутентификация"], summary="Регистрация нового пользователя", dependencies=[Depends(authlim)])
def reg(data: useradd, db: Session = Depends(getdb)) -> usr:
    return authserv.reg(db, data)

@router.post("/auth/login", response_model=tokenresp, tags=["Аутентификация"], summary="Аутентификация и получение JWT токена", dependencies=[Depends(authlim)])
def login(data: loginreq, db: Session = Depends(getdb)) -> tokenresp:
    return authserv.auth(db, data)

@router.get("/auth/me", response_model=useresp, tags=["Пользователь"], summary="Получить текущего пользователя")
def me(u: usr = Depends(getactualuser)) -> usr:
    return u

@router.post("/auth/logout", response_model=msgresp, tags=["Аутентификация"], summary="Выход из системы (отзыв токена)")
def logout(cred: HTTPAuthorizationCredentials = Depends(bearer_scheme), db: Session = Depends(getdb)) -> msgresp:
    authserv.logout(db, cred.credentials)
    return msgresp(message="Успешный выход из системы. Токен отозван.")

