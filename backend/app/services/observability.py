"""Serviço simples de observabilidade e SLOs."""

from __future__ import annotations

from statistics import mean


class ObservabilityStore:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.latencies_ms: list[float] = []
        self.total_requests = 0
        self.total_errors = 0

    def record(self, *, latency_ms: float, status_code: int) -> None:
        self.total_requests += 1
        self.latencies_ms.append(latency_ms)
        if status_code >= 400:
            self.total_errors += 1

    def summary(self) -> dict:
        total = self.total_requests
        avg_latency = round(mean(self.latencies_ms), 2) if self.latencies_ms else 0.0
        p95_latency = 0.0
        if self.latencies_ms:
            ordered = sorted(self.latencies_ms)
            index = min(len(ordered) - 1, max(0, int(len(ordered) * 0.95) - 1))
            p95_latency = round(ordered[index], 2)
        availability = round(((total - self.total_errors) / total) * 100, 2) if total else 100.0
        error_rate = round((self.total_errors / total) * 100, 2) if total else 0.0

        incidents: list[dict] = []
        if error_rate > 5:
            incidents.append({"tipo": "erro", "mensagem": "Taxa de erro acima do limite de 5%"})
        if avg_latency > 300:
            incidents.append({"tipo": "latencia", "mensagem": "Latência média acima de 300ms"})

        return {
            "requests_total": total,
            "errors_total": self.total_errors,
            "availability_pct": availability,
            "error_rate_pct": error_rate,
            "avg_latency_ms": avg_latency,
            "p95_latency_ms": p95_latency,
            "slo_targets": {
                "availability_pct": 99.5,
                "avg_latency_ms": 300,
                "error_rate_pct": 5.0,
            },
            "incidents_open": len(incidents),
            "incidents": incidents,
        }


observability_store = ObservabilityStore()
