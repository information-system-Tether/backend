import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from kb.database import Base, SessionLocal, engine
from kb.seed_kb import seedkb
from kb.models import kbarticle

def init_kb_db():
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seedkb(db)
    print("Knowledge base database initialized.")

if __name__ == "__main__":
    init_kb_db()
