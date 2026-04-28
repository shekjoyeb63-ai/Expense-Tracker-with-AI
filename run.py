from app import create_app
from app.services.celery_worker import make_celery

app = create_app()
celery = make_celery(app)

if __name__ == "__main__":
    app.run(debug=True)