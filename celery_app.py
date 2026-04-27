import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

flask_app = create_app()

from app import celery

app = celery