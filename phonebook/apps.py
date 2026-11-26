from django.apps import AppConfig


class PhonebookConfig(AppConfig):
    name = 'phonebook'
    verbose_name = 'Książka telefoniczna'

    def ready(self):
        from . import signals  # noqa: F401
