from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from documents.models import Category

EDITORS_GROUP = 'Redaktorzy dokumentów'
DEFAULT_CATEGORIES = ['BHP', 'Kadry i płace', 'Urlopy i czas pracy', 'IT i bezpieczeństwo', 'Ogólne']


class Command(BaseCommand):
    help = 'Tworzy grupę redaktorów dokumentów oraz domyślne kategorie.'

    def handle(self, *args, **options):
        group, _ = Group.objects.get_or_create(name=EDITORS_GROUP)
        perms = Permission.objects.filter(
            content_type__app_label='documents',
            codename__in=['add_document', 'change_document', 'delete_document', 'view_document',
                          'add_category', 'change_category', 'view_category'],
        )
        group.permissions.set(perms)
        self.stdout.write(f'Grupa „{EDITORS_GROUP}”: {perms.count()} uprawnień.')

        for name in DEFAULT_CATEGORIES:
            _, created = Category.objects.get_or_create(name=name)
            if created:
                self.stdout.write(f'  + kategoria {name}')
        self.stdout.write(self.style.SUCCESS('Gotowe.'))
