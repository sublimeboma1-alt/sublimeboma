import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from .models import CodeJeton


SESSION_JETON_KEY = 'finance_jeton_code'
SESSION_JETON_USER_KEY = 'finance_jeton_user_id'


def active_finance_jeton(request):
    """Return the token stored in this user's server-side session, if valid."""
    code = request.session.get(SESSION_JETON_KEY)
    if not code or request.session.get(SESSION_JETON_USER_KEY) != request.user.id:
        return None
    jeton = CodeJeton.objects.filter(code=code).select_related(
        'niveau', 'classe', 'type_frais', 'annee_scolaire', 'trimestre'
    ).first()
    if not jeton or not jeton.est_valide():
        request.session.pop(SESSION_JETON_KEY, None)
        request.session.pop(SESSION_JETON_USER_KEY, None)
        return None
    return jeton


def finance_jeton_required(view):
    """Protect every financial API even when it is called outside the UI."""
    def wrapped(request, *args, **kwargs):
        request.finance_jeton = active_finance_jeton(request)
        if not request.finance_jeton:
            return JsonResponse({'detail': 'Un code jeton finance valide est requis.'}, status=403)
        return view(request, *args, **kwargs)
    return wrapped


def scope_frais(queryset, jeton):
    """Apply non-negotiable token constraints to a FraisScolaire queryset."""
    if jeton.annee_scolaire_id:
        queryset = queryset.filter(annee_scolaire_id=jeton.annee_scolaire_id)
    if jeton.niveau_id:
        queryset = queryset.filter(niveau_id=jeton.niveau_id)
    if jeton.classe_id:
        queryset = queryset.filter(eleve__classe_id=jeton.classe_id)
    if jeton.type_frais_id:
        queryset = queryset.filter(type_frais_id=jeton.type_frais_id)
    if jeton.trimestre_id:
        queryset = queryset.filter(trimestre_id=jeton.trimestre_id)
    return queryset


def scope_tarifs(queryset, jeton):
    """Apply the fields that exist directly on a TarifFrais queryset."""
    if jeton.annee_scolaire_id:
        queryset = queryset.filter(annee_scolaire_id=jeton.annee_scolaire_id)
    if jeton.niveau_id:
        queryset = queryset.filter(niveau_id=jeton.niveau_id)
    if jeton.type_frais_id:
        queryset = queryset.filter(type_frais_id=jeton.type_frais_id)
    if jeton.trimestre_id:
        queryset = queryset.filter(trimestre_id=jeton.trimestre_id)
    return queryset


@csrf_protect
@require_http_methods(['POST'])
@login_required
def valider_jeton(request):
    """Valide un code jeton et retourne son perimetre d'acces."""
    try:
        data = json.loads(request.body or '{}')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'valide': False, 'message': 'Requete invalide.'}, status=400)

    code = (data.get('code') or '').strip().upper()
    if not code:
        return JsonResponse({'valide': False, 'message': 'Veuillez saisir un code jeton.'}, status=400)

    jeton = CodeJeton.objects.filter(code=code).select_related(
        'niveau', 'classe', 'type_frais', 'annee_scolaire', 'trimestre'
    ).first()

    if not jeton:
        return JsonResponse({'valide': False, 'message': 'Code jeton introuvable.'}, status=404)

    if not jeton.est_valide():
        return JsonResponse({'valide': False, 'message': 'Ce jeton est expire ou desactive.'}, status=403)

    # Marquer le jeton comme utilise
    jeton.marquer_utilise(user=request.user)
    # The browser may be modified; the real authorization is kept server-side.
    request.session[SESSION_JETON_KEY] = jeton.code
    request.session[SESSION_JETON_USER_KEY] = request.user.id

    # Construire le perimetre d'acces
    perimetre = {
        'valide': True,
        'code': jeton.code,
        'description': jeton.description or '',
        'niveau_code': jeton.niveau_id,
        'niveau_libelle': str(jeton.niveau) if jeton.niveau else None,
        'classe_id': jeton.classe_id,
        'classe_nom': str(jeton.classe) if jeton.classe else None,
        'type_frais_code': jeton.type_frais_id,
        'type_frais_libelle': str(jeton.type_frais) if jeton.type_frais else None,
        'annee_scolaire_id': jeton.annee_scolaire_id,
        'annee_scolaire': str(jeton.annee_scolaire) if jeton.annee_scolaire else None,
        'trimestre_numero': jeton.trimestre_id,
        'trimestre_libelle': str(jeton.trimestre) if jeton.trimestre else None,
    }

    return JsonResponse(perimetre)


@csrf_protect
@require_http_methods(['POST'])
@login_required
def quitter_jeton(request):
    request.session.pop(SESSION_JETON_KEY, None)
    request.session.pop(SESSION_JETON_USER_KEY, None)
    return JsonResponse({'ok': True})
