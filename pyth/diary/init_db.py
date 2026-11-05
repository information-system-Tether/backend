import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from diary.database import Base, SessionLocal, addcols, engine
from diary.baseproducts import seedbase
from diary.models import *

def init_diary_db():
    Base.metadata.create_all(bind=engine)
    addcols()
    with SessionLocal() as db:
        seedbase(db)
    print("Diary database initialized.")

if __name__ == "__main__":
    init_diary_db()
