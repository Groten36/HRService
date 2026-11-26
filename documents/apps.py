from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    name = 'documents'
    verbose_name = 'Dokumenty'

    def ready(self):
        from . import signals  # noqa: F401
