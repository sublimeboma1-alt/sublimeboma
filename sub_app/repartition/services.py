from decimal import Decimal, ROUND_HALF_UP

from sub_app.frais_scolaires.models import Paiement

from .models import LigneRepartition, ParametreRepartition, RegleRepartition


def create_payment_distribution(paiement):
    if paiement.statut_id != 'valide' or LigneRepartition.objects.filter(paiement=paiement).exists():
        return
    type_frais = paiement.frais.type_frais
    parameter = ParametreRepartition.objects.filter(type_frais=type_frais, annee_scolaire=paiement.frais.annee_scolaire, est_actif=True).first()
    if not parameter:
        return
    rules = list(RegleRepartition.objects.select_related('categorie').filter(parametre=parameter, est_active=True, categorie__est_active=True).order_by('categorie__ordre', 'id'))
    if not rules or sum((rule.pourcentage for rule in rules), Decimal('0')) != Decimal('100'):
        return
    remaining = paiement.montant_paye
    rows = []
    for index, rule in enumerate(rules):
        amount = remaining if index == len(rules) - 1 else (paiement.montant_paye * rule.pourcentage / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        remaining -= amount
        rows.append(LigneRepartition(paiement=paiement, categorie=rule.categorie, pourcentage=rule.pourcentage, montant=amount))
    LigneRepartition.objects.bulk_create(rows)


def rebuild_distributions_for_parameter(parameter):
    """Apply a parameter to every validated payment already in its school year."""
    if not parameter.est_actif or not parameter.annee_scolaire_id:
        return 0

    payments = Paiement.objects.select_related('frais__type_frais').filter(
        statut_id='valide',
        frais__annee_scolaire_id=parameter.annee_scolaire_id,
        frais__type_frais_id=parameter.type_frais_id,
    )
    LigneRepartition.objects.filter(paiement__in=payments).delete()
    for payment in payments:
        create_payment_distribution(payment)
    return payments.count()
