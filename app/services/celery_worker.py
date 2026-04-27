from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()  

def make_celery(app):
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    celery = Celery(
        app.import_name,
        broker=redis_url,
        backend=redis_url
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery