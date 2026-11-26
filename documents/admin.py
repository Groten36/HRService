from django.contrib import admin

from .models import Category, Document


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ['name']}
    search_fields = ['name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'kind', 'number', 'category', 'is_published', 'effective_date', 'created_at']
    list_filter = ['kind', 'category', 'is_published']
    search_fields = ['title', 'number', 'description']
    readonly_fields = ['original_filename', 'uploaded_by', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.uploaded_by = request.user
        if 'file' in form.changed_data and obj.file:
            obj.original_filename = obj.file.name.rsplit('/', 1)[-1]
        super().save_model(request, obj, form, change)
