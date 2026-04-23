# Telemetry Service

Сервис для сбора и анализа телеметрии с устройств (показания x, y, z). Реализует синхронную и асинхронную (Celery) аналитику, нагрузочное тестирование Locust, развёртывание через Docker Compose.

## Выполненные пункты технического задания

### 1. Сбор статистики с устройства по его идентификатору

Эндпоинт `POST /devices/{device_id}/stats/` принимает JSON `{"x": float, "y": float, "z": float}` и сохраняет показание с временной меткой.

### 2. Анализ статистики устройства за определённый период и за всё время

Эндпоинт `GET /devices/{device_id}/stats/?start=...&end=...` возвращает вычисленные характеристики.

### 3. Результаты анализа – числовые характеристики

Для величин x, y, z возвращаются `min`, `max`, `count`, `sum`, `median`.

### 4. Добавление пользователей устройств

`POST /users/` – создание пользователя.  
`POST /users/{user_id}/devices/` – создание устройства, привязанного к пользователю.

### 5. Аналитика по идентификатору пользователя

`GET /users/{user_id}/stats/?start=...&end=...` выдаёт:
- `total` – агрегированные результаты для всех устройств пользователя
- `per_device` – результаты для каждого устройства отдельно

### 6. Архитектура REST

Все эндпоинты спроектированы по принципам REST (ресурсы, методы HTTP, статус-коды).

### 7. Фреймворк FastAPI

Сервис написан на FastAPI, используется асинхронность (async/await).

### 8. База данных

По умолчанию SQLite (локально), в Docker Compose используется PostgreSQL. Работа через SQLAlchemy (async).

### 9. Асинхронная аналитика через Celery

Реализована с использованием Celery и Redis как брокера.  
Эндпоинты:  
- `POST /devices/{device_id}/stats/async/` – запуск аналитики по устройству  
- `POST /devices/users/{user_id}/stats/async/` – запуск аналитики по пользователю  
- `GET /devices/tasks/{task_id}/` – получение результата

### 10. Нагрузочное тестирование Locust

Сценарий в `locustfile.py`. Результаты приведены ниже.

### 11. Развёртывание через Docker + docker-compose

В корне проекта присутствуют `Dockerfile` и `docker-compose.yml`.

## Инструкция по запуску

### Локально (для разработки)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
docker run -d --name redis -p 6379:6379 redis:7-alpine   # требуется Docker
celery -A app.celery_app worker --pool=solo --loglevel=info   # отдельный терминал
uvicorn app.main:app --reload
