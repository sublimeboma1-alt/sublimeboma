from django.http import JsonResponse

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
    return JsonResponse({'application': 'sublime', 'status': 'ok'})


def identite_etablissement(request):
    return JsonResponse(serialize_identite(IdentiteEtablissement.active()))
