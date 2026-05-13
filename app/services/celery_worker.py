import os
from celery import Celery

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("REDIS_URL")
celery.conf.result_backend = os.environ.get("REDIS_URL")

celery.autodiscover_tasks(['app.services'])

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