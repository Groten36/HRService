"""Główna konfiguracja URL projektu hrservice.

Pliki z MEDIA_ROOT celowo NIE są serwowane publicznie — dokumenty
pobiera się wyłącznie przez widok documents:download, który sprawdza logowanie.
"""
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'HR Service — administracja'
admin.site.site_title = 'HR Service'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dokumenty/', include('documents.urls')),
    path('telefony/', include('phonebook.urls')),
    path('', include('pages.urls')),
]
