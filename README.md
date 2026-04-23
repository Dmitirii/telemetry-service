markdown

# Telemetry Service

REST API для сбора и анализа телеметрии с устройств (показания x, y, z).  
Реализует синхронную и асинхронную (Celery) аналитику, нагрузочное тестирование Locust, развёртывание через Docker Compose.

## Соответствие техническому заданию

### Функциональные требования

1. **Сбор статистики с устройства по его идентификатору** – эндпоинт `POST /devices/{device_id}/stats/` принимает JSON вида `{"x": float, "y": float, "z": float}` и сохраняет показание с временной меткой.

2. **Анализ статистики устройства за определённый период и за всё время** – эндпоинт `GET /devices/{device_id}/stats/?start=...&end=...` возвращает вычисленные характеристики.

3. **Результаты анализа – числовые характеристики** – возвращаются `min`, `max`, `count`, `sum`, `median` для каждой из величин `x`, `y`, `z`.

4. **Добавление пользователей устройств** – `POST /users/` создаёт пользователя, `POST /users/{user_id}/devices/` создаёт устройство, привязанное к пользователю.

5. **Аналитика по идентификатору пользователя** – `GET /users/{user_id}/stats/?start=...&end=...` выдаёт:
   - `total` – агрегированные результаты для всех устройств пользователя
   - `per_device` – результаты для каждого устройства отдельно

Асинхронный вариант аналитики реализован через Celery:  
`POST /devices/{device_id}/stats/async/` и `POST /devices/users/{user_id}/stats/async/` возвращают `task_id`, результат доступен по `GET /devices/tasks/{task_id}/`.

### Нефункциональные требования

- **Архитектура REST** – все эндпоинты спроектированы по принципам REST.
- **Фреймворк FastAPI** – сервис написан на FastAPI, используется асинхронность.
- **Хранение данных** – по умолчанию SQLite (локально), в Docker Compose используется PostgreSQL.
- **Асинхронная аналитика через Celery** – реализована (Redis как брокер).
- **Нагрузочное тестирование Locust** – сценарий в `locustfile.py`, результаты приведены ниже.
- **Развёртывание через Docker + docker-compose** – присутствуют `Dockerfile` и `docker-compose.yml`.

## Инструкция по запуску

### Локально (для разработки)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker run -d --name redis -p 6379:6379 redis:7-alpine   # требуется Docker
celery -A app.celery_app worker --pool=solo --loglevel=info   # в отдельном терминале
uvicorn app.main:app --reload

Через Docker Compose (рекомендованный способ)
bash

docker-compose up --build

Сервис будет доступен по адресу http://localhost:8000, документация API – http://localhost:8000/docs.
Нагрузочное тестирование

Запуск:
bash

locust -f locustfile.py --host=http://localhost:8000

Результаты (10 пользователей, spawn rate 1, длительность ~5 минут):
Эндпоинт	RPS	Средняя задержка (ms)	95-й перцентиль (ms)	Ошибки
POST /users/	0.24	2054	2100	0%
POST /users/{id}/devices/	0.02	20	37	0%
POST /devices/{id}/stats/	0.17	21	130	0%
GET /devices/{id}/stats/ (синхронный)	0.14	5	8	0%
POST /devices/{id}/stats/async/	0.02	5	8	0%
GET /tasks/{task_id}/	0.10	6	9	0%

Общие показатели:

    Всего запросов: 203

    Ошибки: 0 (0.00%)

    Средний RPS: 4.86

    Среднее время ответа по всем запросам: 115 ms

Медиана и другие процентили указаны в детальной таблице, прилагаемой к результатам тестирования (доступна в выводе Locust).
Архитектура проекта
text

telemetry_service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI приложение, lifespan
│   ├── database.py             # асинхронный движок SQLAlchemy
│   ├── models.py               # ORM модели User, Device, Stat
│   ├── schemas.py              # Pydantic схемы
│   ├── crud.py                 # CRUD операции и вычисления статистики
│   ├── celery_app.py           # конфигурация Celery
│   ├── tasks.py                # фоновые задачи (аналитика)
│   └── routes/
│       ├── users.py            # эндпоинты пользователей и устройств
│       └── stats.py            # эндпоинты статистики и асинхронных задач
├── requirements.txt
├── locustfile.py
├── Dockerfile
├── docker-compose.yml
└── README.md

API Endpoints
Метод	Эндпоинт	Описание
POST	/users/	Создание пользователя
POST	/users/{user_id}/devices/	Создание устройства для пользователя
POST	/devices/{device_id}/stats/	Отправка показания
GET	/devices/{device_id}/stats/	Синхронная аналитика по устройству
POST	/devices/{device_id}/stats/async/	Асинхронная аналитика по устройству
POST	/devices/users/{user_id}/stats/async/	Асинхронная аналитика по пользователю
GET	/devices/tasks/{task_id}/	Получение результата асинхронной задачи
Используемые технологии

    Python 3.11

    FastAPI

    SQLAlchemy 2.0 (async)

    SQLite / PostgreSQL

    Celery 5.6

    Redis

    Locust 2.43

    Docker, Docker Compose

Результаты тестирования (кратко)

    Максимальная нагрузка: 10 пользователей, генерация 1 пользователь/сек.

    Пропускная способность: сервер выдержал >200 запросов за время теста без ошибок.

    Запись одного показания: в среднем 20 мс.

    Синхронная аналитика устройства: в среднем 6 мс.

    Асинхронная аналитика: ответ на запуск задачи ~5 мс, результат готов за 2-3 секунды.

    Надёжность: 0% ошибок при всех тестовых сценариях.
