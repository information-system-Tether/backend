from datetime import datetime, timezone
import jwt
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from auth.models import badtok, usr
from auth.schemas import loginreq, tokenresp, useradd
from auth.security import createtokenaccess, decodetoken, hashpass, verpass

class authserv:
    @staticmethod
    def reg(db: Session, data: useradd) -> usr:
        u = db.scalar(select(usr).where((usr.login == data.login) | (usr.email == data.email)))
        if u:
            if u.login == data.login:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким логином уже существует")
            if u.email == data.email:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким email уже существует")
        u = usr(login=data.login, email=data.email, password_hash=hashpass(data.password))
        db.add(u)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с такими данными уже существует")
        db.refresh(u)
        return u

    @staticmethod
    def auth(db: Session, data: loginreq) -> tokenresp:
        u = db.scalar(select(usr).where(usr.login == data.login))
        if u is None or not verpass(data.password, u.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
        tok = createtokenaccess(u.id)
        return tokenresp(access_token=tok)

    @staticmethod
    def getuser(db: Session, tok: str) -> usr:
        try:
            claims = decodetoken(tok)
            idu = int(claims["sub"])
            jti = claims.get("jti")
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный или истёкший токен")

        if jti:
            rev = db.scalar(select(badtok).where(badtok.jti == jti))
            if rev:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен был отозван. Выполните повторный вход.")

        u = db.get(usr, idu)
        if u is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
        return u

    @staticmethod
    def logout(db: Session, tok: str) -> None:
        try:
            claims = decodetoken(tok)
            idu = int(claims["sub"])
            jti = claims.get("jti")
            exp = claims.get("exp")
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else datetime.now(timezone.utc)
        except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

        if not jti:
            return

        rev = db.scalar(select(badtok).where(badtok.jti == jti))
        if not rev:
            rev = badtok(jti=jti, user_id=idu, expires_at=exp_dt)
            db.add(rev)
            db.commit()

