# Tether Backend

Микросервисный бэкенд для мобильного приложения учета питания, контроля суточного баланса калорий и макронутриентов (КБЖУ), расчета антропометрических норм здоровья и персональной базы знаний.

Вся сопутствующая информация, структура проекта, схемы взаимодействия и детальное описание каждого сервиса и исходного файла находятся в папке [**`/docs`**](file:///D:/Tether/docs) и файле [**`docs/tree.md`**](file:///D:/Tether/docs/tree.md).

Данный README.md создан в ознакомительных целях. Более подробная информация находится в .md файлах в директории /docs.

---

## Архитектура системы

Бэкенд спроектирован по модульной микросервисной схеме на базе FastAPI. Каждый микросервис отвечает за свою предметную область, работает автономно и может быть развернут как в контейнерах Docker, так и локально.

```text
[Клиент: мобильное приложение или веб]
│
├─ Порт 8001: Auth Service (аутентификация, JWT, управление сессиями)
│  └─ [docs/service/auth.md]
│
├─ Порт 8002: Diary Service (дневник питания, КБЖУ, профиль здоровья, продукты)
│  └─ [docs/service/diary.md]
│
├─ Порт 8003: Knowledge Base Service (справочник, статьи, полнотекстовый поиск)
│  └─ [docs/service/kb.md]
│
└─ Инфраструктура хранения и управления:
   ├─ Порт 5432: PostgreSQL 18 (база данных) [docs/service/db.md]
   └─ Порт 8080: pgAdmin 4 (веб-панель СУБД) [docs/service/pg.md]
```

Сквозная авторизация между клиентом и сервисами реализована по стандарту **JWT Bearer**: пользователь авторизуется в сервисе Auth и получает токен, а сервис Diary автономно проверяет токен по общему ключу подписи без дополнительных межсервисных вызовов.

---

## Стек технологий

- **Язык программирования:** Python 3.12
- **Веб-фреймворк:** FastAPI (ASGI-сервер Uvicorn)
- **СУБД:** PostgreSQL 18 (в Docker-окружении) / SQLite (для автономного локального запуска)
- **ORM и доступ к данным:** SQLAlchemy 2.0, psycopg 3
- **Валидация данных:** Pydantic v2, pydantic-settings
- **Безопасность и криптография:** PyJWT, bcrypt, встроенный Rate Limiter
- **Контейнеризация:** Docker, Docker Compose (мультимодульная конфигурация через `include`)

---

## Навигация по документации

Вся подробная проектная документация размещена в каталоге [**`docs/`**](file:///D:/Tether/docs):

- [**Руководство по запуску (docs/README.md)**](file:///D:/Tether/docs/README.md) — подробные инструкции по запуску через Docker Compose и через скрипт `run_backend.py`, переменные окружения, решение типовых проблем.
- [**Дерево файлов и структура проекта (docs/tree.md)**](file:///D:/Tether/docs/tree.md) — общее дерево файлов репозитория, дерево `.md` документов, назначение всех папок и файлов.
- [**Реестр вопросов базы знаний (docs/rosterofquestions.md)**](file:///D:/Tether/docs/rosterofquestions.md) — полный список 113 вопросов базы знаний, загружаемых по умолчанию.
- [**Микросервис Auth (docs/service/auth.md)**](file:///D:/Tether/docs/service/auth.md) — регистрация, авторизация, JWT, черный список токенов, эндпоинты и разбор файлов `.py`.
- [**Микросервис Diary (docs/service/diary.md)**](file:///D:/Tether/docs/service/diary.md) — дневник, формулы BMR/TDEE, расчет норм КБЖУ, продукты, избранное, статистика и разбор файлов `.py`.
- [**Микросервис KB (docs/service/kb.md)**](file:///D:/Tether/docs/service/kb.md) — база знаний, полнотекстовый поиск, категоризация, пагинация и разбор файлов `.py`.
- [**База данных PostgreSQL (docs/service/db.md)**](file:///D:/Tether/docs/service/db.md) — описание СУБД, параметры подключения, healthcheck и volume `pgdata`.
- [**Панель pgAdmin 4 (docs/service/pg.md)**](file:///D:/Tether/docs/service/pg.md) — доступ к веб-панели управления базой данных на порту 8080.

---

## Быстрый старт

### Вариант 1. Запуск через Docker (рекомендуемый)

Требуется установленный Docker:

```bash
# Сборка образов и запуск всех сервисов в фоновом режиме:
docker compose up -d --build

# Проверка статуса (должно быть 5 работающих контейнеров):
docker compose ps
```

### Вариант 2. Запуск через run_backend.py (без Docker)

Автономный запуск на встроенной базе SQLite (`tether.db`):

```bash
# 1. Создание и активация виртуального окружения:
python -m venv venv
.\venv\Scripts\activate   # Windows PowerShell / cmd
# source venv/bin/activate # Linux / macOS

# 2. Установка зависимостей:
pip install -r pyth/requirements.txt

# 3. Запуск всех сервисов:
python run_backend.py
```

*Тестовый аккаунт:* логин `tester`, пароль `tester`.

---

## Порты сервисов и интерактивная документация

| Сервис | Порт | Базовый URL | Swagger UI (Интерактивная документация) | Документация сервиса |
| :--- | :---: | :--- | :--- | :--- |
| **Auth Service** | `8001` | `http://localhost:8001` | [http://localhost:8001/docs](http://localhost:8001/docs) | [docs/service/auth.md](file:///D:/Tether/docs/service/auth.md) |
| **Diary Service** | `8002` | `http://localhost:8002` | [http://localhost:8002/docs](http://localhost:8002/docs) | [docs/service/diary.md](file:///D:/Tether/docs/service/diary.md) |
| **KB Service** | `8003` | `http://localhost:8003` | [http://localhost:8003/docs](http://localhost:8003/docs) | [docs/service/kb.md](file:///D:/Tether/docs/service/kb.md) |
| **PostgreSQL** | `5432` | `localhost:5432` | — *(сервер базы данных)* | [docs/service/db.md](file:///D:/Tether/docs/service/db.md) |
| **pgAdmin 4** | `8080` | `http://localhost:8080` | [http://localhost:8080](http://localhost:8080) (логин: `adm@mail.ru`, пароль: `P@ssw0rd`) | [docs/service/pg.md](file:///D:/Tether/docs/service/pg.md) |
