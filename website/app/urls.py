from django.urls import path, include
from . import views


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/installations/toggle', views.toggle_installation, name='toggle_installation'),
    path('dashboard/installations/reset_time_limit', views.reset_time_limit, name='reset_time_limit'),
    path('dashboard/installations/update_data', views.update_data, name='update_data'),
    path('dashboard/installations/command_pending', views.command_pending, name='command_pending'),
    path('dashboard/installations/set_pressure_target', views.set_pressure_target, name='set_pressure_target'),
    path('', include('django.contrib.auth.urls')),
]







