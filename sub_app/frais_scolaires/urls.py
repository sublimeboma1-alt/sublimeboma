from django.urls import path
from . import views

app_name = 'frais_scolaire'

urlpatterns = [
    # Tableau de bord
    path('', views.dashboard_frais, name='dashboard_frais'),
    path('dashboard/', views.dashboard_frais, name='dashboard_frais'),
    
    # Configuration année scolaire
    path('configurer-annee/', views.configurer_annee, name='configurer_annee'),
    
    # Configuration des tarifs
    path('configurer-tarifs/', views.configurer_tarifs, name='configurer_tarifs'),
    path('supprimer-tarif/<int:pk>/', views.supprimer_tarif, name='supprimer_tarif'),
    path('appliquer-tarifs/', views.appliquer_tarifs_eleves, name='appliquer_tarifs'),
    
    # Gestion des élèves (frais)
    path('eleves/', views.liste_eleves_frais, name='liste_eleves_frais'),
    path('eleve/<int:pk>/', views.detail_eleve_frais, name='detail_eleve_frais'),
    path('eleve/<int:eleve_id>/ajouter-frais/', views.ajouter_frais_manuel, name='ajouter_frais_manuel'),
    
    # Paiements
    path('eleve/<int:eleve_id>/paiement/', views.enregistrer_paiement, name='enregistrer_paiement'),
    path('eleve/<int:eleve_id>/paiement/<int:frais_id>/', views.enregistrer_paiement, name='enregistrer_paiement_frais'),
    path('paiement/imprimer/<int:paiement_id>/', views.imprimer_recu, name='imprimer_recu'),
    
    # Statistiques
    path('statistiques/', views.statistiques_frais, name='statistiques'),
    path('comparaison-masp/', views.comparaison_paiements_masp, name='comparaison_masp'),
    path('export-excel/', views.export_statistiques_excel, name='export_statistiques_excel'),
    path('export-pdf/', views.export_statistiques_pdf, name='export_statistiques_pdf'),

    #################################################"
    path('export-comparaison-masp-excel/', views.export_comparaison_masp_excel, name='export_comparaison_masp_excel'),
    path('export-comparaison-masp-pdf/', views.export_comparaison_masp_pdf, name='export_comparaison_masp_pdf'),
]