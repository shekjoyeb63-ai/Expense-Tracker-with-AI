#!/bin/bash
PYTHONPATH=/app celery -A celery_app worker --loglevel=info --pool=solo &
gunicorn run:app --bind 0.0.0.0:$PORT --workers 2