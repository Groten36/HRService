from django.urls import path

from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='list'),
    path('programy/', views.DocumentListView.as_view(kind='software'), name='software'),
    path('kategoria/<slug:slug>/', views.DocumentListView.as_view(), name='category'),
    path('dodaj/', views.DocumentCreateView.as_view(), name='create'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/pobierz/', views.DocumentDownloadView.as_view(), name='download'),
    path('<int:pk>/edytuj/', views.DocumentUpdateView.as_view(), name='update'),
    path('<int:pk>/usun/', views.DocumentDeleteView.as_view(), name='delete'),
]
