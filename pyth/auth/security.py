from datetime import datetime, timedelta, timezone
import uuid
import bcrypt
import jwt
from auth.config import getcfg

def hashpass(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verpass(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def createtokenaccess(user_id: int) -> str:
    cfg = getcfg()
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=cfg.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "jti": uuid.uuid4().hex,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
    }
    return jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)

def decodetoken(tok: str) -> dict:
    cfg = getcfg()
    return jwt.decode(tok, cfg.jwt_secret_key, algorithms=[cfg.jwt_algorithm])
