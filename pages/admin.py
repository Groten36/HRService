from django.contrib import admin

from .models import LinkGroup, UsefulLink


class UsefulLinkInline(admin.TabularInline):
    model = UsefulLink
    extra = 1
    fields = ['title', 'url', 'description', 'order', 'is_active']


@admin.register(LinkGroup)
class LinkGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    list_editable = ['order']
    inlines = [UsefulLinkInline]


@admin.register(UsefulLink)
class UsefulLinkAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'url', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['group', 'is_active']
    search_fields = ['title', 'url', 'description']
