from django.contrib import admin

from .models import Department, Employee, Section


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    inlines = [SectionInline]


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'department']
    list_filter = ['department']
    search_fields = ['name', 'department__name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'department', 'section', 'position', 'phone', 'room', 'email']
    list_display_links = ['last_name', 'first_name']
    list_filter = ['department', 'section']
    search_fields = ['first_name', 'last_name', 'phone', 'email', 'room', 'position']
    autocomplete_fields = ['department', 'section']
    fieldsets = [
        (None, {'fields': [('first_name', 'last_name'), ('department', 'section'), 'position']}),
        ('Kontakt', {'fields': [('phone', 'room'), 'email']}),
    ]
