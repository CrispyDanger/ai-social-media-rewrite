from django.apps import AppConfig


class SpaceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    label = 'space'
    name = 'apps.space'

    def ready(self):
        from . import signals  # noqa: F401
