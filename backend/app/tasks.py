"""
Celery application bootstrap.

Mantém o worker e o beat operacionais no ambiente interno da Sprint 15,
mesmo enquanto a fila assíncrona ainda evolui por incrementos.
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery = Celery(
    "gestao_apoio_arquivistico",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"],
)

celery.conf.update(
    task_default_queue="default",
    broker_connection_retry_on_startup=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "heartbeat-operacional": {
            "task": "app.tasks.heartbeat_operacional",
            "schedule": 300.0,
        }
    },
)

# Alias aceito pelo CLI do Celery com `-A app.tasks`
app = celery


@celery.task(name="app.tasks.heartbeat_operacional")
def heartbeat_operacional() -> dict[str, str]:
    """Tarefa periódica simples para validar o barramento assíncrono."""
    return {"status": "ok", "task": "heartbeat_operacional"}