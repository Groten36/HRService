from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from accounts.roles import set_role

# Konta przykładowe do testów lokalnych — dane logowania opisane w README.md.
DEMO_USERS = [
    # (login, hasło, rola lub None dla superużytkownika, imię, nazwisko)
    ('admin', 'Admin!2026', None, 'Adam', 'Administrator'),
    ('it', 'AdminIT!2026', 'it_admin', 'Igor', 'Informatyk'),
    ('kadry', 'AdminHR!2026', 'hr_admin', 'Karolina', 'Kadrowa'),
    ('anna', 'Pracownik!2026', 'employee', 'Anna', 'Nowak'),
]


class Command(BaseCommand):
    help = 'Tworzy przykładowe konta (superużytkownik, Administrator IT, Administrator HR, Pracownik).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset', action='store_true',
            help='Dla istniejących kont przywróć hasło i rolę z listy przykładowych.',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Pozwól uruchomić przy DEBUG=False (nie rób tego na produkcji).',
        )

    def handle(self, *args, reset=False, force=False, **options):
        if not settings.DEBUG and not force:
            raise CommandError('Konta przykładowe mają znane hasła — tylko przy DEBUG=True (lub --force).')

        User = get_user_model()
        for username, password, role, first_name, last_name in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first_name, 'last_name': last_name,
                          'email': f'{username}@example.com'},
            )
            if not created and not reset:
                self.stdout.write(f'  = {username} (istnieje, bez zmian)')
                continue
            user.set_password(password)
            user.is_active = True
            user.is_superuser = user.is_staff = role is None
            user.save()
            if role:
                set_role(user, role)
            self.stdout.write(f'  + {username} ({"utworzono" if created else "zresetowano"})')
        self.stdout.write(self.style.SUCCESS('Gotowe.'))
