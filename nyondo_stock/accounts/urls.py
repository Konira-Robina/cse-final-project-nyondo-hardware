from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('register/', views.register_user_view, name='register_user'),
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('logout/', views.logout_confirm, name='logout_confirm'),
    path('logout/confirm/', views.logout_view, name='logout'),
]