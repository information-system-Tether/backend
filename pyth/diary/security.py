import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from diary.config import getcfg

bearer_scheme = HTTPBearer(scheme_name="JWT Bearer", description="Bearer JWT токен")

def getactualuid(cred: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> int:
    cfg = getcfg()
    try:
        claims = jwt.decode(cred.credentials, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
        return int(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный или истекший токен авторизации")

def veradm(key: str = Header(..., alias="X-Admin-Key", description="Секретный ключ администратора")) -> str:
    cfg = getcfg()
    if key != cfg.admin_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен: неверный административный ключ")
    return key
