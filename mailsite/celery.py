import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mailsite.settings')
app = Celery('mailsite')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()