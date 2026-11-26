from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    name = 'accounts'
    verbose_name = 'Konta i role'

    def ready(self):
        from .roles import sync_roles

        # Uruchamiane raz, po migracji ostatniej aplikacji (wtedy istnieją wszystkie uprawnienia)
        def _sync(sender, **kwargs):
            if sender.name == 'hr':
                sync_roles(**kwargs)

        post_migrate.connect(_sync, dispatch_uid='accounts_sync_roles')
