import os
from celery import Celery

def make_celery():
    celery = Celery(
        'app',
        broker=os.environ.get("REDIS_URL"),
        backend=os.environ.get("REDIS_URL"),
        include=['app.services.tasks']
    )
    return celery

celery = make_celery()