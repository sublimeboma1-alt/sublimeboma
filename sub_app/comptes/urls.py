from django.urls import path

from . import views


app_name = 'comptes'

urlpatterns = [
    path('api/session/', views.session_view, name='session'),
    path('api/login/', views.login_view, name='login'),
    path('api/logout/', views.logout_view, name='logout'),
]
