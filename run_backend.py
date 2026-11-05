import os
import sys
import subprocess
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

backend_dir = os.path.dirname(os.path.abspath(__file__))
pyth_dir = os.path.join(backend_dir, "pyth")
db_path = os.path.join(backend_dir, "tether.db").replace("\\", "/")
database_url = f"sqlite:///{db_path}"

env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
env["DATABASE_URL"] = database_url
env["PYTHONPATH"] = pyth_dir

print("=" * 60)
print("Initializing Tether Backend (SQLite)...")
print("Database URL:", database_url)
print("=" * 60)

# 1. Создаем тестового пользователя и базовые таблицы авторизации
try:
    init_auth = [sys.executable, os.path.join(pyth_dir, "auth", "testuser.py")]
    subprocess.run(init_auth, env=env, check=True)
except Exception as e:
    print("Auth init warning:", e)

# 2. Инициализируем таблицы дневника и базовый справочник продуктов
try:
    init_diary = [sys.executable, os.path.join(pyth_dir, "diary", "init_db.py")]
    subprocess.run(init_diary, env=env, check=True)
except Exception as e:
    print("Diary init warning:", e)

if "--init-only" in sys.argv or "--check" in sys.argv:
    print("\nBackend initialization verified successfully.")
    sys.exit(0)

print("\n" + "=" * 60)
print("Tether Backend running on:")
print("  - Auth Service  : http://localhost:8001  (Docs: http://localhost:8001/docs)")
print("  - Diary Service : http://localhost:8002  (Docs: http://localhost:8002/docs)")
print("  - Test User     : login 'tester', password 'tester'")
print("=" * 60 + "\n")

auth_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "auth.main:app", "--host", "0.0.0.0", "--port", "8001"],
    env=env,
    cwd=pyth_dir
)

diary_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "diary.main:app", "--host", "0.0.0.0", "--port", "8002"],
    env=env,
    cwd=pyth_dir
)

try:
    while True:
        time.sleep(1)
        if auth_proc.poll() is not None or diary_proc.poll() is not None:
            break
except KeyboardInterrupt:
    print("\nStopping services...")
finally:
    auth_proc.terminate()
    diary_proc.terminate()
    print("Services stopped.")
