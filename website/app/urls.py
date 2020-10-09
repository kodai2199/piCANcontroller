from django.urls import path, include
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/installations/toggle', views.toggle_installation, name='toggle_installation'),
    path('dashboard/installations/reset_time_limit', views.reset_time_limit, name='reset_time_limit'),
    path('', include('django.contrib.auth.urls')),
]







