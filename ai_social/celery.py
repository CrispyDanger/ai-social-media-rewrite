import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_social.settings.local')

app = Celery('ai_social')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.beat_schedule = {
    'bots-schedule-turns': {
        'task': 'apps.bots.tasks.schedule_bot_turns',
        'schedule': 60.0,
    },
}
app.autodiscover_tasks()
