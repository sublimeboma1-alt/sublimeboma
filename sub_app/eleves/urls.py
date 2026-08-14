from django.urls import path

from . import views


app_name = 'eleves'

urlpatterns = [
    path('api/classes/', views.classes_list, name='classes_list'),
    path('api/references/', views.references_view, name='references'),
    path('api/eleves/export/xlsx/', views.export_eleves_xlsx, name='eleves_export_xlsx'),
    path('api/eleves/', views.eleves_list_create, name='eleves_list_create'),
    path('api/eleves/<int:eleve_id>/', views.eleve_detail, name='eleve_detail'),
]
