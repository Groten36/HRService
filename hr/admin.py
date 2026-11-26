from django.contrib import admin
from django.contrib.auth.models import User

from accounts.admin import RoleAwareUserAdmin

from .models import Announcement, EmployeeProfile, LeaveRequest


class EmployeeProfileInline(admin.StackedInline):
    model = EmployeeProfile
    fk_name = 'user'
    can_delete = False
    verbose_name_plural = 'Profil kadrowy'
    autocomplete_fields = ['phonebook_entry', 'manager']


admin.site.unregister(User)


@admin.register(User)
class HRUserAdmin(RoleAwareUserAdmin):
    inlines = [EmployeeProfileInline]


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'employee_number', 'contract_type', 'hire_date', 'annual_leave_days',
                    'carried_over_days', 'manager']
    list_filter = ['contract_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_number']
    autocomplete_fields = ['user', 'phonebook_entry', 'manager']


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'leave_type', 'start_date', 'end_date', 'days', 'status', 'created_at']
    list_filter = ['status', 'leave_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    readonly_fields = ['days', 'created_at', 'reviewed_at']
    date_hierarchy = 'start_date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_pinned', 'is_published', 'created_by', 'created_at']
    list_filter = ['is_pinned', 'is_published']
    search_fields = ['title', 'body']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
