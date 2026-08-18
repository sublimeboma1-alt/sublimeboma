import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import CategorieDepense
from sub_app.frais_scolaires.jeton_views import finance_jeton_required


def health(request):
    return JsonResponse({'application': 'depense', 'status': 'ok'})


@login_required
@finance_jeton_required
@require_http_methods(['GET'])
def categories(request):
    rows = CategorieDepense.objects.all()
    return JsonResponse({'results': [{'id': item.id, 'nom': item.nom, 'description': item.description or ''} for item in rows]})
