from collections.abc import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from diary.config import getcfg

engine = create_engine(getcfg().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def getdb() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def addcols() -> None:
    with engine.begin() as conn:
        for col in ("product_type VARCHAR(32)", "base_product_id INTEGER", "user_product_id INTEGER", "quantity_grams NUMERIC(8, 2)", "weight NUMERIC(6, 2)", "water NUMERIC(8, 2)"):
            conn.execute(text(f"ALTER TABLE entries ADD COLUMN IF NOT EXISTS {col}"))
        conn.execute(text("UPDATE entries SET water = ROUND(quantity_grams / 1000.0, 2) WHERE product_type = 'beverages' AND quantity_grams IS NOT NULL AND (water IS NULL OR water = 0)"))
        conn.execute(text("UPDATE entries SET water = 0 WHERE water IS NULL"))

