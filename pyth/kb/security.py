from fastapi import Header, HTTPException, status
from kb.config import getcfg

def veradm(key: str = Header(..., alias="X-Admin-Key", description="Секретный ключ администратора")) -> str:
    cfg = getcfg()
    if key != cfg.admin_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен: неверный административный ключ")
    return key
