from django.urls import path

from . import views

urlpatterns = [
    path('profil/', views.ProfileView.as_view(), name='profile'),
    path('uzytkownicy/', views.UserListView.as_view(), name='user_list'),
    path('uzytkownicy/dodaj/', views.UserCreateView.as_view(), name='user_create'),
    path('uzytkownicy/<int:pk>/edytuj/', views.UserUpdateView.as_view(), name='user_update'),
    path('uzytkownicy/<int:pk>/haslo/', views.UserSetPasswordView.as_view(), name='user_password'),
    path('uzytkownicy/<int:pk>/usun/', views.UserDeleteView.as_view(), name='user_delete'),
]
