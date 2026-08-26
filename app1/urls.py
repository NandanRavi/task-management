from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProjectView,
    TaskView,
    UserListView
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),

    # Project endpoints
    path('projects/', ProjectView.as_view(), name='project-list-create'),
    path('projects/<uuid:pk>/', ProjectView.as_view(), name='project-detail'),

    # Task endpoints
    path('tasks/', TaskView.as_view(), name='task-list-create'),
    path('tasks/<uuid:pk>/', TaskView.as_view(), name='task-detail'),

    # User endpoints
    path('users/', UserListView.as_view(), name='user-list'),
]