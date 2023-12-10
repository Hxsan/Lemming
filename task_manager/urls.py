"""
URL configuration for task_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/create_team', views.create_team, name = "create_team"),
    path('dashboard/show_team/<int:team_id>/', views.show_team, name = "show_team"),
    path('dashboard/show_team/<int:team_id>/user_activity_log/<int:user_id>', views.user_activity_log, name = "activity_log"),
    path('dashboard/view-task/<int:team_id>/<int:task_id>/', views.view_task, name='view_task'),
    path('notification_hub/', views.notification_hub, name='notification_hub'),
    path('log_in/', views.LogInView.as_view(), name='log_in'),
    path('log_out/', views.log_out, name='log_out'),
    path('password/', views.PasswordView.as_view(), name='password'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
    path('sign_up/', views.SignUpView.as_view(), name='sign_up'),
    path('dashboard/create_task/<int:pk>/', views.CreateTaskView.as_view(), name='create_task'),
    path('dashboard/view-task/<int:task_id>/remove_task/', views.remove_task, name='remove_task'),
    path('dashboard/show_team/<int:team_id>/remove_member/<str:member_username>/', views.remove_member, name='remove_member'),
    path('delete-team/<int:team_id>/', views.delete_team, name='delete_team'),
    path('dashboard/view-task/submit_time/<int:team_id>/<int:task_id>/', views.submit_time, name='submit_time'),
    path('dashboard/view-task/reset_time/<int:team_id>/<int:task_id>/', views.reset_time, name='reset_time'),
    path('summary_report/', views.summary_report, name='summary_report'),
]

