from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
import bcrypt
import jwt
from auth.config import getcfg

def hashpass(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verpass(pwd: str, pwdhash: str) -> bool:
    return bcrypt.checkpw(pwd.encode("utf-8"), pwdhash.encode("utf-8"))

def createtokenaccess(idu: int) -> str:
    cfg = getcfg()
    exp = datetime.now(timezone.utc) + timedelta(minutes=cfg.jwt_access_token_expire_minutes)
    claims = {"sub": str(idu), "jti": str(uuid.uuid4()), "exp": exp, "iat": datetime.now(timezone.utc)}
    return jwt.encode(claims, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)

def decodetoken(tok: str) -> dict[str, Any]:
    cfg = getcfg()
    return jwt.decode(tok, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])


