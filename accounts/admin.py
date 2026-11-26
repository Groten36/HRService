from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .roles import ROLE_GROUP_NAMES


class RoleAwareUserAdmin(UserAdmin):
    """Panel użytkowników bezpieczny dla nie-superuserów (Administrator IT).

    - nie widzi pól is_superuser i user_permissions,
    - może przypisać tylko grupy ról,
    - nie może edytować ani usuwać superuserów.
    """

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if request.user.is_superuser:
            return fieldsets
        cleaned = []
        for title, opts in fieldsets:
            fields = [f for f in opts.get('fields', ()) if f not in ('is_superuser', 'user_permissions')]
            cleaned.append((title, {**opts, 'fields': fields}))
        return cleaned

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'groups' and not request.user.is_superuser:
            kwargs['queryset'] = Group.objects.filter(name__in=ROLE_GROUP_NAMES)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_list_filter(self, request):
        filters = super().get_list_filter(request)
        return filters if request.user.is_superuser else [f for f in filters if f != 'is_superuser']

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and (obj == request.user or (obj.is_superuser and not request.user.is_superuser)):
            return False
        return super().has_delete_permission(request, obj)
