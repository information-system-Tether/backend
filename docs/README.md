# Руководство по запуску бэкенда Tether

Данный документ содержит руководство по развертыванию, настройке и запуску бэкенда проекта Tether.

Бэкенд проекта Tether состоит из трех микросервисов: авторизации, дневника питания с расчетом норм КБЖУ и базы знаний.

Вся сопутствующая информация, структура проекта, схемы взаимодействия и детальное описание каждого сервиса и исходного файла находятся в папке [**`/docs`**](file:///D:/Tether/docs) и файле [**`tree.md`**](file:///D:/Tether/docs/tree.md):
- [Дерево файлов проекта и документации (tree.md)](file:///D:/Tether/docs/tree.md)
- [Реестр вопросов базы знаний (rosterofquestions.md)](file:///D:/Tether/docs/rosterofquestions.md)
- [Микросервис Auth (service/auth.md)](file:///D:/Tether/docs/service/auth.md)
- [Микросервис Diary (service/diary.md)](file:///D:/Tether/docs/service/diary.md)
- [Микросервис KB (service/kb.md)](file:///D:/Tether/docs/service/kb.md)
- [Сервис базы данных DB (service/db.md)](file:///D:/Tether/docs/service/db.md)
- [Сервис интерфейса PG (service/pg.md)](file:///D:/Tether/docs/service/pg.md)

---

## Содержание

1. [Архитектура сервисов](#архитектура-сервисов)
2. [Вариант 1: Запуск через Docker и Docker Compose](#вариант-1-запуск-через-docker-и-docker-compose)
   - [Запуск через терминал (консоль)](#запуск-через-терминал-консоль)
   - [Запуск через Docker Desktop (графический интерфейс)](#запуск-через-docker-desktop-графический-интерфейс)
   - [Работа с базой данных через pgAdmin 4](#работа-с-базой-данных-через-pgadmin-4)
3. [Вариант 2: Запуск через run_backend.py (без Docker)](#вариант-2-запуск-через-run_backendpy-без-docker)
   - [Принцип работы скрипта](#принцип-работы-скрипта)
   - [Пошаговый запуск](#пошаговый-запуск)
   - [Тестовая учетная запись](#тестовая-учетная-запись)
4. [Сводная таблица портов и ссылок на API (Swagger)](#сводная-таблица-портов-и-ссылок-на-api-swagger)
5. [Переменные окружения](#переменные-окружения)
6. [Сравнение вариантов запуска](#сравнение-вариантов-запуска)
7. [Решение частых проблем](#решение-частых-проблем)

---

## Архитектура сервисов

```text
[Клиент: мобильное приложение или браузер]
│
├─ Порт 8001: Auth Service (авторизация и пользователи)
│  └─ База данных
│
├─ Порт 8002: Diary Service (дневник питания, КБЖУ, профиль)
│  └─ База данных
│
├─ Порт 8003: Knowledge Base (база знаний и справочник)
│  └─ База данных
│
└─ Инфраструктура:
   ├─ Порт 5432: PostgreSQL (база данных в Docker)
   └─ Порт 8080: pgAdmin 4 (веб-интерфейс базы данных)
```

Подробное описание архитектуры, каждого файла исходного кода и структуры документации содержится в файле [**tree.md**](file:///D:/Tether/docs/tree.md).

---

## Вариант 1: Запуск через Docker и Docker Compose

Этот способ запускает сервисы в изолированных контейнерах с использованием базы данных PostgreSQL 18 и панели pgAdmin 4.

### Требования
- Установленный Docker (Docker Desktop для Windows/macOS или Docker Engine с плагином compose для Linux).
- Запущенная служба Docker.

---

### Запуск через терминал (консоль)

В корневой папке проекта (`d:\Tether`):

1. **Сборка образов и запуск контейнеров:**
   ```bash
   docker compose up -d --build
   ```

2. **Проверка статуса контейнеров:**
   ```bash
   docker compose ps
   ```
   В настоящий момент, должно быть 5 работающих контейнеров:
   - `db` (`dbpostgres`) — статус `healthy`
   - `tether-auth` — `Up` (порт `8001->8000`)
   - `tether-diary` — `Up` (порт `8002->8000`)
   - `tether-kb` — `Up` (порт `8003->8000`)
   - `pg` (`pgadmin4`) — `Up` (порт `8080->80`)

3. **Просмотр логов:**
   ```bash
   # Логи всех сервисов
   docker compose logs -f

   # Логи конкретного сервиса
   docker compose logs -f auth
   docker compose logs -f diary
   docker compose logs -f kb
   ```

4. **Остановка контейнеров:**
   ```bash
   # Обычная остановка
   docker compose down

   # Остановка с удалением сохраненных данных базы
   docker compose down -v
   ```

---

### Запуск через Docker Desktop (графический интерфейс)

1. Открыть приложение **Docker Desktop**.
2. В терминале корневой папки проекта один раз выполнить команду `docker compose up -d`.
3. В интерфейсе Docker Desktop перейти в раздел **Containers**:
   - Отображается группа контейнеров `tether`.
   - Внутри группы находятся 5 сервисов: `db`, `tether-auth`, `tether-diary`, `tether-kb`, `pg`.
4. Доступные действия в интерфейсе:
   - Запуск, остановка и перезапуск всей группы или отдельных контейнеров кнопками управления.
   - Просмотр логов во вкладке **Logs**.
   - Переход на веб-страницу сервиса нажатием на номер порта (например, `8001:8000`).

---

### Работа с базой данных через pgAdmin 4

В состав Docker-окружения входит веб-интерфейс pgAdmin 4:

1. Открыть в браузере: `http://localhost:8080`
2. Данные для входа:
   - **Email:** `adm@mail.ru`
   - **Пароль:** `P@ssw0rd`
3. Подключение к базе данных PostgreSQL:
   - Выбрать пункт **Add New Server** (или *Register -> Server*).
   - Во вкладке **General**:
     - Поле *Name:* `Tether DB`
   - Во вкладке **Connection**:
     - Поле *Host name/address:* `db`
     - Поле *Port:* `5432`
     - Поле *Maintenance database:* `tether`
     - Поле *Username:* `tether`
     - Поле *Password:* `P@ssw0rd`
   - Нажать **Save**. После этого доступны таблицы и возможность выполнения SQL-запросов.

---

## Вариант 2: Запуск через run_backend.py (без Docker)

Вариант запуска без использования Docker и PostgreSQL. Вся система работает локально с базой данных SQLite.

### Принцип работы скрипта

Скрипт `run_backend.py` выполняет следующие действия:
1. Создает локальный файл базы данных SQLite `tether.db` в корне проекта.
2. Инициализирует таблицы авторизации и создает тестового пользователя `tester` с паролем `tester` (`pyth/auth/testuser.py`).
3. Инициализирует таблицы дневника питания и наполняет базу каталогом продуктов с показателями КБЖУ (`pyth/diary/init_db.py`).
4. Инициализирует таблицы базы знаний и загружает статьи (`pyth/kb/init_db.py`).
5. Запускает три сервера Uvicorn:
   - Auth Service: `http://0.0.0.0:8001`
   - Diary Service: `http://0.0.0.0:8002`
   - Knowledge Base: `http://0.0.0.0:8003`
6. При нажатии `Ctrl+C` корректно завершает работу всех трех процессов.

---

### Пошаговый запуск

#### Шаг 1. Проверка версии Python
Требуется Python версии 3.10 или выше (рекомендуется 3.12):
```bash
python --version
```

#### Шаг 2. Создание и активация виртуального окружения
```bash
# В корне проекта (d:\Tether)
python -m venv venv

# Активация в Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Активация в Windows (командная строка cmd):
.\venv\Scripts\activate.bat

# Активация в Linux / macOS:
source venv/bin/activate
```

#### Шаг 3. Установка зависимостей
```bash
pip install -r pyth/requirements.txt
```

#### Шаг 4. Запуск бэкенда
```bash
python run_backend.py
```

При запуске в консоли выводится информационный блок:
```text
Бэкенд-сервер включается...
БД (SQLite): sqlite:///D:/Tether/tether.db
Tester exists.
Login: tester | Password: tester | Token: eyJhbGciOiJIUzI1Ni...
Diary database initialized.
Knowledge base database initialized.

Бэкенд ВКЛ:
  - Auth Service       : http://localhost:8001  (Docs: http://localhost:8001/docs)
  - Diary Service      : http://localhost:8002  (Docs: http://localhost:8002/docs)
  - Knowledge Base (KB): http://localhost:8003  (Docs: http://localhost:8003/docs)
  - Test User          : login 'tester', password 'tester'
```

#### Дополнительные параметры скрипта:
- `python run_backend.py --check` или `python run_backend.py --init-only`: выполняет только создание таблиц и загрузку начальных данных без запуска серверов (применяется для проверки целостности в тестах).

---

### Тестовая учетная запись

При запуске через `run_backend.py` автоматически подготавливается учетная запись для тестирования:
- **Логин:** `tester`
- **Пароль:** `tester`
- **Email:** `tester@tester.test`
- **Токен:** выводится в консоль при старте, либо запрашивается через эндпоинт `POST /auth/login`.

---

## Сводная таблица портов и ссылок на API (Swagger)

| Сервис | Порт | Базовый URL | Документация Swagger UI | Документация сервиса |
| :--- | :---: | :--- | :--- | :--- |
| **Auth Service** | `8001` | `http://localhost:8001` | [http://localhost:8001/docs](http://localhost:8001/docs) | [service/auth.md](file:///D:/Tether/docs/service/auth.md) |
| **Diary Service** | `8002` | `http://localhost:8002` | [http://localhost:8002/docs](http://localhost:8002/docs) | [service/diary.md](file:///D:/Tether/docs/service/diary.md) |
| **Knowledge Base** | `8003` | `http://localhost:8003` | [http://localhost:8003/docs](http://localhost:8003/docs) | [service/kb.md](file:///D:/Tether/docs/service/kb.md) |
| **PostgreSQL** | `5432` | `localhost:5432` | — *(сервер базы данных)* | [service/db.md](file:///D:/Tether/docs/service/db.md) |
| **pgAdmin 4** | `8080` | `http://localhost:8080` | — *(панель управления базой)* | [service/pg.md](file:///D:/Tether/docs/service/pg.md) |

Корневой адрес `/` каждого сервиса настроен на автоматическое перенаправление на страницу документации `/docs`.

---

## Переменные окружения

Значения параметров по умолчанию, используемые в проекте:

| Параметр | Значение по умолчанию | Описание |
| :--- | :--- | :--- |
| `POSTGRES_DB` | `tether` | Имя базы данных PostgreSQL |
| `POSTGRES_USER` | `tether` | Имя пользователя базы данных |
| `POSTGRES_PASSWORD` | `P@ssw0rd` | Пароль пользователя базы данных |
| `DATABASE_URL` | `postgresql+psycopg://tether:P%40ssw0rd@db:5432/tether` | Строка подключения к базе данных |
| `JWT_SECRET_KEY` | `whoarewewhoarewe?moscowpolykek` | Секретный ключ для подписи токенов JWT |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Срок действия токена в минутах |
| `ADMIN_API_KEY` | `tester` | Ключ администратора для управления статьями базы знаний |
| `PGADMIN_DEFAULT_EMAIL` | `adm@mail.ru` | Email для входа в pgAdmin |
| `PGADMIN_DEFAULT_PASSWORD` | `P@ssw0rd` | Пароль для входа в pgAdmin |

---

## Сравнение вариантов запуска

| Параметр | Docker Compose | `run_backend.py` |
| :--- | :--- | :--- |
| **База данных** | PostgreSQL 18 | SQLite (`tether.db`) |
| **Требования к ПО** | Docker Desktop | Python 3.10+ |
| **Изоляция компонентов** | Полная (отдельные контейнеры) | Запуск процессов в общей системе |
| **Интерфейс базы данных** | pgAdmin 4 на порту 8080 | Сторонний просмотрщик файлов SQLite |
| **Основное назначение** | Стандартная работа и командная разработка | Быстрый локальный запуск и мобильная разработка |

---

## Решение частых проблем

### 1. Порт уже занят (ошибка `address already in use`)
Если один из портов (8001, 8002, 8003, 5432, 8080) занят другим процессом:
- В случае предыдущего запуска через Docker выполнить:
  ```bash
  docker compose down
  ```
- В случае зависшего процесса в Windows найти и завершить процесс:
  ```powershell
  netstat -ano | findstr :8001
  taskkill /PID <номер_PID> /F
  ```

### 2. Ошибка сборки `FROM tether-diary:latest not found`
Образ сервиса `kb` собирается на основе слоя `tether-diary`. Сборку следует выполнять для всех сервисов вместе:
```bash
docker compose up -d --build
```

### 3. Ошибка блокировки SQLite `database is locked` при работе через `run_backend.py`
Файловая база SQLite блокируется при одновременной записи из нескольких потоков. При необходимости одновременного активного тестирования нескольких сервисов рекомендуется использовать запуск через Docker с базой данных PostgreSQL.
