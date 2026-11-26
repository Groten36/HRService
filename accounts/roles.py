"""Role użytkowników portalu — każda rola to grupa Django z zestawem uprawnień.

Grupy są tworzone/aktualizowane automatycznie po `migrate` (patrz apps.py).
"""
from dataclasses import dataclass

from django.contrib.auth.models import Group, Permission
from django.db import transaction


@dataclass(frozen=True)
class Role:
    key: str
    name: str            # nazwa grupy Django
    description: str
    is_staff: bool       # dostęp do panelu admina
    permissions: tuple   # 'app_label.codename'


def _crud(app, *models, delete=True):
    actions = ('add', 'change', 'delete', 'view') if delete else ('add', 'change', 'view')
    return tuple(f'{app}.{a}_{m}' for m in models for a in actions)


EMPLOYEE = Role(
    key='employee', name='Pracownik',
    description='Przegląda stronę; w portalu HR czyta ogłoszenia i składa wnioski urlopowe.',
    is_staff=False, permissions=(),
)
IT_ADMIN = Role(
    key='it_admin', name='Administrator IT',
    description='Zarządza użytkownikami, dokumentami, programami i przydatnymi linkami.',
    is_staff=True,
    permissions=(
        *_crud('auth', 'user'),
        *_crud('documents', 'document', 'category'),
        *_crud('pages', 'linkgroup', 'usefullink'),
    ),
)
HR_ADMIN = Role(
    key='hr_admin', name='Administrator HR',
    description='Publikuje ogłoszenia HR, rozpatruje wnioski urlopowe, prowadzi profile kadrowe '
                'i książkę telefoniczną.',
    is_staff=True,
    permissions=(
        'hr.review_leaverequest', 'hr.view_leaverequest', 'hr.change_leaverequest',
        *_crud('hr', 'announcement', 'employeeprofile'),
        *_crud('phonebook', 'employee', 'department', 'section'),
        'auth.view_user',  # wybór użytkownika przy profilu kadrowym
    ),
)

ROLES = (EMPLOYEE, IT_ADMIN, HR_ADMIN)
ROLES_BY_KEY = {r.key: r for r in ROLES}
ROLE_CHOICES = [(r.key, r.name) for r in ROLES]
ROLE_GROUP_NAMES = [r.name for r in ROLES]
LEGACY_GROUPS = ['Redaktorzy dokumentów', 'Kadry (HR)']


def sync_roles(verbosity=0, **kwargs):
    """Tworzy grupy ról i ustawia im dokładnie zdefiniowane uprawnienia."""
    for role in ROLES:
        group, _ = Group.objects.get_or_create(name=role.name)
        perms = []
        for perm in role.permissions:
            app_label, codename = perm.split('.')
            try:
                perms.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
            except Permission.DoesNotExist:
                if verbosity:
                    print(f'  ! brak uprawnienia {perm}')
        group.permissions.set(perms)
    Group.objects.filter(name__in=LEGACY_GROUPS, user__isnull=True).delete()


def get_role(user):
    if user.is_superuser:
        return None
    names = set(user.groups.values_list('name', flat=True))
    # Najwyższa rola wygrywa
    for role in (IT_ADMIN, HR_ADMIN, EMPLOYEE):
        if role.name in names:
            return role
    return None


@transaction.atomic
def set_role(user, role_key):
    role = ROLES_BY_KEY[role_key]
    user.groups.remove(*Group.objects.filter(name__in=ROLE_GROUP_NAMES))
    user.groups.add(Group.objects.get(name=role.name))
    if not user.is_superuser:
        user.is_staff = role.is_staff
        user.save(update_fields=['is_staff'])
