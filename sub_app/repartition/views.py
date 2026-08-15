import json
from datetime import date
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from sub_app.frais_scolaires.models import AnneeScolaire, Paiement, TypeFrais
from .models import CategorieRepartition, LigneRepartition, ParametreRepartition, RegleRepartition
from .services import rebuild_distributions_for_parameter


def request_data(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return {}


def serialize_rules(parameter):
    rules = RegleRepartition.objects.select_related('categorie').filter(parametre=parameter, est_active=True, categorie__est_active=True)
    return [{'categorie_id': rule.categorie_id, 'code': rule.categorie.code, 'libelle': rule.categorie.libelle, 'couleur': rule.categorie.couleur, 'pourcentage': float(rule.pourcentage)} for rule in rules]


def active_year():
    return AnneeScolaire.objects.filter(est_active=True).first()


@login_required
@csrf_protect
@require_http_methods(['GET', 'POST'])
def parametres(request):
    types = list(TypeFrais.objects.filter(est_actif=True).order_by('libelle'))
    year = active_year()
    if request.method == 'POST':
        data = request_data(request)
        type_frais = TypeFrais.objects.filter(code=data.get('type_frais'), est_actif=True).first()
        name = str(data.get('nom', '')).strip()
        allocations = data.get('allocations', [])
        if not year or not type_frais or not name or not isinstance(allocations, list) or not allocations:
            return JsonResponse({'detail': 'Le nom, le type de frais et les repartitions sont obligatoires.'}, status=400)
        try:
            parsed = [(int(item['categorie_id']), Decimal(str(item['pourcentage']))) for item in allocations]
        except (KeyError, TypeError, ValueError, InvalidOperation):
            return JsonResponse({'detail': 'Parametres de repartition invalides.'}, status=400)
        if len({item[0] for item in parsed}) != len(parsed) or any(percent < 0 or percent > 100 for _, percent in parsed):
            return JsonResponse({'detail': 'Chaque pourcentage doit etre compris entre 0 et 100.'}, status=400)
        if sum((percent for _, percent in parsed), Decimal('0')) != Decimal('100'):
            return JsonResponse({'detail': 'Le total des pourcentages doit etre exactement egal a 100 %.'}, status=400)
        categories = {item.id: item for item in CategorieRepartition.objects.filter(id__in=[category_id for category_id, _ in parsed], est_active=True)}
        if len(categories) != len(parsed):
            return JsonResponse({'detail': 'Une categorie selectionnee est introuvable ou inactive.'}, status=400)
        with transaction.atomic():
            parameter, _ = ParametreRepartition.objects.update_or_create(type_frais=type_frais, annee_scolaire=year, defaults={'nom': name, 'est_actif': True})
            RegleRepartition.objects.filter(parametre=parameter).delete()
            RegleRepartition.objects.bulk_create([RegleRepartition(parametre=parameter, type_frais=type_frais, categorie=categories[category_id], pourcentage=percent) for category_id, percent in parsed])
            payments_processed = rebuild_distributions_for_parameter(parameter)
        return JsonResponse({
            'id': parameter.id,
            'nom': parameter.nom,
            'type_frais': type_frais.code,
            'allocations': serialize_rules(parameter),
            'paiements_repartis': payments_processed,
        })
    parameters = ParametreRepartition.objects.select_related('type_frais').prefetch_related('regles__categorie').filter(annee_scolaire=year) if year else ParametreRepartition.objects.none()
    return JsonResponse({
        'categories': [{'id': item.id, 'code': item.code, 'libelle': item.libelle, 'couleur': item.couleur} for item in CategorieRepartition.objects.filter(est_active=True)],
        'types_frais': [{'code': item.code, 'libelle': item.libelle} for item in types],
        'annee_scolaire': {'id': year.id, 'annee': year.annee} if year else None,
        'parametres': [{'id': item.id, 'nom': item.nom, 'type_frais': item.type_frais_id, 'type_frais_libelle': item.type_frais.libelle, 'est_actif': item.est_actif, 'allocations': serialize_rules(item)} for item in parameters],
    })


@login_required
@require_http_methods(['GET'])
def dashboard(request):
    type_frais = request.GET.get('type_frais', '')
    date_start = request.GET.get('date_debut', '')
    date_end = request.GET.get('date_fin', '')
    year = active_year()
    lines = LigneRepartition.objects.select_related('paiement__frais__type_frais', 'paiement__eleve', 'categorie').filter(paiement__statut_id='valide')
    if year:
        lines = lines.filter(paiement__frais__annee_scolaire=year)
    else:
        lines = lines.none()
    parameter_id = request.GET.get('parametre_id', '')
    parameters = ParametreRepartition.objects.select_related('type_frais').filter(annee_scolaire=year, est_actif=True) if year else ParametreRepartition.objects.none()
    if not parameters.exists():
        lines = lines.none()
    if parameter_id:
        parameter = parameters.filter(id=parameter_id).first()
        if not parameter:
            return JsonResponse({'detail': 'Parametre introuvable pour l annee scolaire active.'}, status=400)
        lines = lines.filter(paiement__frais__type_frais=parameter.type_frais)
    if type_frais:
        lines = lines.filter(paiement__frais__type_frais_id=type_frais)
    if date_start:
        lines = lines.filter(paiement__date_paiement__gte=date_start)
    if date_end:
        lines = lines.filter(paiement__date_paiement__lte=date_end)
    total = lines.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    by_category = []
    for category in CategorieRepartition.objects.filter(est_active=True):
        amount = lines.filter(categorie=category).aggregate(total=Sum('montant'))['total'] or Decimal('0')
        by_category.append({'id': category.id, 'libelle': category.libelle, 'couleur': category.couleur, 'amount': float(amount), 'percent': round(float(amount / total * 100), 1) if total else 0})
    payments = {}
    for line in lines.order_by('-paiement__date_paiement', '-paiement_id', 'categorie__ordre')[:300]:
        payment = line.paiement
        item = payments.setdefault(payment.id, {'id': payment.id, 'reference': payment.reference, 'date': payment.date_paiement.isoformat(), 'eleve': f'{payment.eleve.nom} {payment.eleve.post_nom} {payment.eleve.prenom}'.strip(), 'type_frais': str(payment.frais.type_frais), 'amount': float(payment.montant_paye), 'allocations': []})
        item['allocations'].append({'libelle': line.categorie.libelle, 'couleur': line.categorie.couleur, 'pourcentage': float(line.pourcentage), 'montant': float(line.montant)})
    today = date.today()
    today_total = lines.filter(paiement__date_paiement=today).aggregate(total=Sum('montant'))['total'] or Decimal('0')
    return JsonResponse({'annee_scolaire': {'id': year.id, 'annee': year.annee} if year else None, 'parametres': [{'id': item.id, 'nom': item.nom, 'type_frais': item.type_frais_id} for item in parameters], 'total': float(total), 'today_total': float(today_total), 'payment_count': len(payments), 'by_category': by_category, 'payments': list(payments.values())})
