from locust import HttpUser, task, between
import random

class TelemetryUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Создаём пользователя и устройство при старте каждого воркера
        resp = self.client.post("/users/", json={"name": f"load_user_{random.randint(1,100000)}"})
        self.user_id = resp.json().get("id")
        resp_dev = self.client.post(f"/users/{self.user_id}/devices/", json={"name": "load_device"})
        self.device_id = resp_dev.json().get("id")

    @task(3)
    def send_stats(self):
        # Отправка показаний
        data = {"x": random.uniform(0,100), "y": random.uniform(0,100), "z": random.uniform(0,100)}
        self.client.post(f"/devices/{self.device_id}/stats/", json=data)

    @task(2)
    def get_device_stats(self):
        # Получение аналитики по устройству за последние сутки
        self.client.get(f"/devices/{self.device_id}/stats/?start=2026-04-23T00:00:00&end=2026-04-23T23:59:59")

    @task(1)
    def get_user_stats(self):
        # Получение аналитики по пользователю
        self.client.get(f"/users/{self.user_id}/stats/?start=2026-04-23T00:00:00&end=2026-04-23T23:59:59")