from sqlalchemy import select
from auth.database import engine, SessionLocal
from auth.models import Base, usr
from auth.security import createtokenaccess, hashpass

def mktestuser():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        u = db.scalar(select(usr).where(usr.login == "tester"))
        if not u:
            print("Создание пользователя для теста...")
            u = usr(login="tester", email="test@test", password_hash=hashpass("tester"))
            db.add(u)
            db.commit()
            db.refresh(u)
        else:
            print("Tester exists.")
        tok = createtokenaccess(u.id)
        print("Login: tester | Password: tester | Token:", tok)

if __name__ == "__main__":
    mktestuser()

