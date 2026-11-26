from django.core.management.base import BaseCommand

from accounts.roles import ROLES, sync_roles


class Command(BaseCommand):
    help = 'Tworzy/aktualizuje grupy ról (uruchamiane też automatycznie po migrate).'

    def handle(self, *args, **options):
        sync_roles(verbosity=1)
        for role in ROLES:
            self.stdout.write(f'  {role.name}: {len(role.permissions)} uprawnień — {role.description}')
        self.stdout.write(self.style.SUCCESS('Gotowe.'))
