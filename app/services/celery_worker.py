from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery(
    "app",
    broker=redis_url,
    backend=redis_url,
    include=["app.services.tasks"]  # ← explicitly tell celery where tasks are
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

def make_celery(app):
    celery.conf.update(
        broker_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        result_backend=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery