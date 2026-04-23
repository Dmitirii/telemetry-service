# Telemetry Service

Сервис для сбора и анализа телеметрии с устройств (показания x, y, z).  
Реализует синхронную и асинхронную (Celery) аналитику, нагрузочное тестирование Locust, развёртывание через Docker Compose.

## 

### Функциональные требования

1. **Сбор статистики с устройства** – `POST /devices/{device_id}/stats/` принимает `{"x": float, "y": float, "z": float}`.
2. **Анализ статистики устройства за период** – `GET /devices/{device_id}/stats/?start=...&end=...` возвращает `min`, `max`, `count`, `sum`, `median` для x,y,z.
3. **Результаты анализа – числовые характеристики** – все пять величин присутствуют в ответе.
4. **Добавление пользователей и устройств** – `POST /users/`, `POST /users/{id}/devices/`.
5. **Аналитика по пользователю** – `GET /users/{id}/stats/` выдаёт агрегацию по всем устройствам (`total`) и отдельно по каждому (`per_device`).
6. **Асинхронная аналитика через Celery** – `POST /devices/{id}/stats/async/`, `POST /devices/users/{id}/stats/async/` возвращают `task_id`, результат по `GET /devices/tasks/{task_id}/`. Брокер – Redis.

### Нефункциональные требования

- **Архитектура REST** – все эндпоинты спроектированы по REST, используют соответствующие HTTP-методы и статусы.
- **Фреймворк FastAPI** – сервис написан на FastAPI с полной асинхронностью (async/await).
- **Хранение данных** – по умолчанию SQLite, в Docker Compose используется PostgreSQL (SQLAlchemy async).
- **Асинхронная аналитика через Celery** – реализована, Redis используется как брокер сообщений.
- **Нагрузочное тестирование Locust** – сценарий в `locustfile.py`, результаты тестирования приведены ниже.
- **Развёртывание через Docker + docker-compose** – в корне присутствуют `Dockerfile` и `docker-compose.yml`, одной командой поднимается вся инфраструктура.

## Инструкция по запуску

### Локально (для разработки)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker run -d --name redis -p 6379:6379 redis:7-alpine   # требуется Docker
celery -A app.celery_app worker --pool=solo --loglevel=info   # отдельный терминал
uvicorn app.main:app --reload
```

## Через Docker Compose
```bash

docker-compose up --build
```

### После запуска сервис доступен: http://localhost:8000, документация – http://localhost:8000/docs.

## Нагрузочное тестирование

### Запуск:
```bash

locust -f locustfile.py --host=http://localhost:8000
```


### Результаты (10 пользователей, spawn rate 1):
Эндпоинт	RPS	Средняя задержка (ms)	95-й перцентиль (ms)	Ошибки
POST /users/	0.24	2054	2100	0%
POST /users/{id}/devices/	0.02	20	37	0%
POST /devices/{id}/stats/	0.17	21	130	0%
GET /devices/{id}/stats/ (синхронный)	0.14	5	8	0%
POST /devices/{id}/stats/async/	0.02	5	8	0%
GET /tasks/{task_id}/	0.10	6	9	0%

### Общие показатели:

    Всего запросов: 203

    Ошибки: 0 (0.00%)

    Средний RPS: 4.86

    Среднее время ответа: 115 ms

### Архитектура проекта

```text

telemetry_service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── crud.py
│   ├── celery_app.py
│   ├── tasks.py
│   └── routes/
│       ├── __init__.py
│       ├── users.py
│       └── stats.py
├── requirements.txt
├── locustfile.py
├── Dockerfile
├── docker-compose.yml
└── README.md
```

Список всех эндпоинтов
Метод	Эндпоинт	Описание
POST	/users/	Создать пользователя
POST	/users/{user_id}/devices/	Добавить устройство пользователю
POST	/devices/{device_id}/stats/	Отправить показание
GET	/devices/{device_id}/stats/	Синхронная аналитика устройства
POST	/devices/{device_id}/stats/async/	Асинхронная аналитика устройства
POST	/devices/users/{user_id}/stats/async/	Асинхронная аналитика пользователя
GET	/devices/tasks/{task_id}/	Получить результат асинхронной задачи

## Используемые технологии

    Python 3.11

    FastAPI

    SQLAlchemy 2.0 (async)

    SQLite / PostgreSQL

    Celery 5.6

    Redis

    Locust 2.43

    Docker, Docker Compose

Ссылка на репозиторий

https://github.com/Dmitirii/telemetry-service
