from django.http import JsonResponse
from django.shortcuts import render

from .models import IdentiteEtablissement


def serialize_identite(identite):
    if not identite:
        return {
            'nom': 'Complexe Scolaire Sublime',
            'espace': 'Administration',
            'sigle': 'CS',
            'adresse': '',
            'telephone': '',
            'email': '',
        }

    return {
        'id': identite.id,
        'nom': identite.nom,
        'espace': identite.espace,
        'sigle': identite.sigle,
        'adresse': identite.adresse,
        'telephone': identite.telephone,
        'email': identite.email,
    }


def home(request):
    """Rend le build React situe dans frontend/dist/index.html."""
    return render(request, 'index.html')


def identite_etablissement(request):
    return JsonResponse(serialize_identite(IdentiteEtablissement.active()))
