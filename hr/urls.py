from django.urls import path

from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('ogloszenia/', views.AnnouncementListView.as_view(), name='announcements'),
    path('ogloszenia/dodaj/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
    path('ogloszenia/<int:pk>/', views.AnnouncementDetailView.as_view(), name='announcement_detail'),
    path('ogloszenia/<int:pk>/edytuj/', views.AnnouncementUpdateView.as_view(), name='announcement_update'),
    path('ogloszenia/<int:pk>/usun/', views.AnnouncementDeleteView.as_view(), name='announcement_delete'),
    path('moje-dane/', views.MyProfileView.as_view(), name='my_profile'),
    path('urlopy/', views.MyLeaveListView.as_view(), name='leave_list'),
    path('urlopy/nowy/', views.LeaveCreateView.as_view(), name='leave_create'),
    path('urlopy/<int:pk>/', views.LeaveDetailView.as_view(), name='leave_detail'),
    path('urlopy/<int:pk>/anuluj/', views.LeaveCancelView.as_view(), name='leave_cancel'),
    path('urlopy/do-rozpatrzenia/', views.LeaveReviewListView.as_view(), name='leave_review'),
]
