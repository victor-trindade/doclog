from django.apps import AppConfig
from time import sleep


class DocConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        import app.signals
        from .tasks import start_scheduler
        start_scheduler()