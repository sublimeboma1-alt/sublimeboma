from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import AnneeScolaire, FraisScolaire, ModePaiement, Paiement


def serialize_paiement(paiement):
    eleve = paiement.eleve
    return {
        'id': paiement.id,
        'reference': paiement.reference,
        'frais_id': paiement.frais_id,
        'eleve_id': paiement.eleve_id,
        'name': f'{eleve.nom} {eleve.post_nom} {eleve.prenom}'.strip() if eleve else 'Élève supprimé',
        'amount': float(paiement.montant_paye),
        'date': paiement.date_paiement.isoformat(),
        'method': str(paiement.mode_paiement),
        'agent': paiement.agent.get_username() if paiement.agent else '',
        'status': paiement.statut_id,
    }


def serialize_dossier(eleve, frais):
    total = sum((f.montant_total for f in frais), Decimal('0'))
    paid = sum((f.total_paye for f in frais), Decimal('0'))
    first_unpaid = next((f for f in frais if f.solde_restant > 0), None)
    classe = eleve.classe
    niveau = str(classe.niveau) if classe and classe.niveau else ''
    option = ''
    if classe and classe.niveau_id == 'humanite' and classe.section:
        option = str(classe.section)
    return {
        'id': eleve.id,
        'eleve_id': eleve.id,
        'frais_id': first_unpaid.id if first_unpaid else (frais[0].id if frais else None),
        'name': f'{eleve.nom} {eleve.post_nom} {eleve.prenom}'.strip(),
        'matricule': eleve.matricule,
        'classe': str(eleve.classe) if eleve.classe else 'Non assigne',
        'niveau': niveau,
        'option': option,
        'total': float(total),
        'paid': float(paid),
        'balance': float(total - paid),
        'statut': 'paid' if total > 0 and paid >= total else 'late' if paid == 0 else 'partial',
        'masp': eleve.est_masp,
    }


def serialize_frais(frais):
    return {
        'id': frais.id,
        'trimestre': str(frais.trimestre),
        'trimestre_numero': frais.trimestre_id,
        'type_frais': str(frais.type_frais),
        'type_frais_code': frais.type_frais_id,
        'montant': float(frais.montant_total),
        'paid': float(frais.total_paye),
        'balance': float(frais.solde_restant),
        'statut': frais.statut_paiement,
        'paiements': [serialize_paiement(p) for p in frais.paiements.all()],
    }


def serialize_eleve_detail(eleve, frais):
    total = sum((f.montant_total for f in frais), Decimal('0'))
    paid = sum((f.total_paye for f in frais), Decimal('0'))
    classe = eleve.classe
    trimestres = {}
    for f in frais:
        key = str(f.trimestre_id)
        if key not in trimestres:
            trimestres[key] = {'trimestre': str(f.trimestre), 'total': Decimal('0'), 'paid': Decimal('0'), 'frais': []}
        trimestres[key]['total'] += f.montant_total
        trimestres[key]['paid'] += Decimal(str(f.total_paye))
        trimestres[key]['frais'].append(serialize_frais(f))
    return {
        'id': eleve.id,
        'name': f'{eleve.nom} {eleve.post_nom} {eleve.prenom}'.strip(),
        'matricule': eleve.matricule,
        'classe': str(eleve.classe) if eleve.classe else 'Non assigne',
        'niveau': str(classe.niveau) if classe and classe.niveau else '',
        'option': str(classe.section) if classe and classe.niveau_id == 'humanite' and classe.section else '',
        'total': float(total),
        'paid': float(paid),
        'balance': float(total - paid),
        'statut': 'paid' if total > 0 and paid >= total else 'late' if paid == 0 else 'partial',
        'masp': eleve.est_masp,
        'annee_scolaire': str(eleve.annee_scolaire) if eleve.annee_scolaire else '',
        'trimestres': [dict(value, total=float(value['total']), paid=float(value['paid']), balance=float(value['total'] - value['paid'])) for value in trimestres.values()],
    }


def clean_paiement_payload(payload, user):
    try:
        frais = FraisScolaire.objects.select_related('eleve').get(id=payload.get('frais_id'))
    except (FraisScolaire.DoesNotExist, TypeError, ValueError):
        raise ValidationError({'frais_id': 'Frais introuvable.'})
    try:
        amount = Decimal(str(payload.get('montant_paye', '0')))
    except Exception:
        raise ValidationError({'montant_paye': 'Montant invalide.'})
    if amount <= 0:
        raise ValidationError({'montant_paye': 'Le montant doit etre superieur a zero.'})
    if amount > frais.solde_restant:
        raise ValidationError({'montant_paye': 'Le montant depasse le solde restant.'})
    mode_code = payload.get('mode_paiement')
    mode = ModePaiement.objects.filter(code=mode_code, est_actif=True).first() if mode_code else ModePaiement.objects.filter(est_actif=True).first()
    if not mode:
        raise ValidationError({'mode_paiement': 'Mode de paiement introuvable.'})
    return Paiement(frais=frais, eleve=frais.eleve, montant_paye=amount, mode_paiement=mode, description=payload.get('description', ''), agent=user)
