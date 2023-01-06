# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ['celery_app']

## Startup
# wsl$ sudo service redis-server start
# psh1$ celery -A core worker -l INFO -P eventlet
# psh2$ py .\manage.py runserver