from django.urls import path

from . import views

urlpatterns = [
    path('rejestracja/', views.SignUpView.as_view(), name='signup'),
    path('profil/', views.ProfileView.as_view(), name='profile'),
]
