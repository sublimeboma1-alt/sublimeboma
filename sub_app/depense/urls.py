from django.urls import path

from . import views


app_name = 'depense'

urlpatterns = [
    path('api/health/', views.health, name='health'),
    path('api/categories/', views.categories, name='categories'),
]
