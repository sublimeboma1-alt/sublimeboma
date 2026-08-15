from django.apps import AppConfig


class RepartitionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sub_app.repartition'

    def ready(self):
        from . import signals  # noqa: F401
