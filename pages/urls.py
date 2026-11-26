from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('o-nas/', views.AboutView.as_view(), name='about'),
    path('kontakt/', views.ContactView.as_view(), name='contact'),
]
