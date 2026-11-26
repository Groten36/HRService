from django.core.management.base import BaseCommand

from documents.models import Category

DEFAULT_CATEGORIES = ['BHP', 'Kadry i płace', 'Urlopy i czas pracy', 'IT i bezpieczeństwo', 'Ogólne']


class Command(BaseCommand):
    help = 'Tworzy domyślne kategorie dokumentów (role tworzy setup_roles / migrate).'

    def handle(self, *args, **options):
        for name in DEFAULT_CATEGORIES:
            _, created = Category.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f'  + kategoria {name}')
        self.stdout.write(self.style.SUCCESS('Gotowe.'))
