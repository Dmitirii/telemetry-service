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

**Асинхронный вариант аналитики (Celery):**  
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
