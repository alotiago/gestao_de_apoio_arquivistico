import os

from locust import HttpUser, between, task


class ApiSmokeUser(HttpUser):
    host = os.getenv("BASE_URL", "http://localhost:8000")
    wait_time = between(0.5, 1.5)

    def on_start(self) -> None:
        self.auth_headers: dict[str, str] = {}

        access_token = os.getenv("ACCESS_TOKEN")
        if access_token:
            self.auth_headers = {"Authorization": f"Bearer {access_token}"}
            return

        auth_username = os.getenv("AUTH_USERNAME")
        auth_password = os.getenv("AUTH_PASSWORD")
        if not auth_username or not auth_password:
            return

        with self.client.post(
            "/api/v1/auth/login",
            data={"username": auth_username, "password": auth_password},
            name="POST /api/v1/auth/login",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Falha de autenticação: HTTP {response.status_code}")
                return

            try:
                body = response.json()
            except ValueError:
                response.failure("Falha de autenticação: resposta inválida")
                return

            token = body.get("access_token")
            if not token:
                response.failure("Falha de autenticação: access_token ausente")
                return

            self.auth_headers = {"Authorization": f"Bearer {token}"}
            response.success()

    @task(4)
    def health_check(self) -> None:
        self.client.get("/health", name="GET /health")

    @task(3)
    def readiness_check(self) -> None:
        self.client.get("/ready", name="GET /ready")

    @task(2)
    def metrics_summary(self) -> None:
        self.client.get("/metrics/summary", name="GET /metrics/summary")

    @task(1)
    def smoke_check(self) -> None:
        if not self.auth_headers:
            return
        self.client.get("/health/smoke", headers=self.auth_headers, name="GET /health/smoke")