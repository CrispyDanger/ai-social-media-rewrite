from django.apps import AppConfig


class BotsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    label = 'bots'
    name = 'apps.bots'

    def ready(self):
        from . import signals  # noqa: F401
