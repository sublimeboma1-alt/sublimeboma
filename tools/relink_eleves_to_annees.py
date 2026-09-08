#!/usr/bin/env python
"""Associe les eleves importes a leur annee scolaire existante."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Relie les eleves importes aux annees scolaires")
    parser.add_argument("--dry-run", action="store_true", help="Affiche le nombre d'eleves concernes sans modifier la base")
    arguments = parser.parse_args()

    if not os.environ.get("DATABASE_PUBLIC_URL"):
        print("DATABASE_PUBLIC_URL doit contenir l'URL PostgreSQL.", file=sys.stderr)
        return 2

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sublime.settings")
    sys.path.insert(0, str(ROOT))
    import django

    django.setup()
    from django.db import transaction
    from django.db.models import OuterRef, Subquery
    from sub_app.eleves.models import Eleve
    from sub_app.frais_scolaires.models import AnneeScolaire, FraisScolaire

    missing_year = Eleve.objects.filter(annee_scolaire__isnull=True)
    fee_year = FraisScolaire.objects.filter(eleve_id=OuterRef('pk')).order_by('annee_scolaire_id').values('annee_scolaire_id')[:1]
    eleves_with_fees = FraisScolaire.objects.exclude(eleve_id=None).values('eleve_id')
    linked_by_fees = missing_year.filter(id__in=eleves_with_fees).count()
    linked_by_date = 0
    active_year = AnneeScolaire.objects.filter(est_active=True).first()

    if arguments.dry_run:
        for eleve in missing_year.filter(frais_inscription__isnull=True).only('id', 'date_inscription'):
            if eleve.date_inscription and AnneeScolaire.objects.filter(date_debut__lte=eleve.date_inscription, date_fin__gte=eleve.date_inscription).exists():
                linked_by_date += 1
        print(f"Eleves sans annee scolaire : {missing_year.count()}")
        print(f"- relies par leurs frais : {linked_by_fees}")
        print(f"- relies par leur date d'inscription : {linked_by_date}")
        print(f"- relies a l'annee active en dernier recours : {active_year.annee if active_year else 'aucune'}")
        return 0

    with transaction.atomic():
        fees_updated = missing_year.filter(id__in=eleves_with_fees).update(annee_scolaire_id=Subquery(fee_year))
        date_updated = 0
        for eleve in Eleve.objects.filter(annee_scolaire__isnull=True).only('id', 'date_inscription'):
            year = AnneeScolaire.objects.filter(date_debut__lte=eleve.date_inscription, date_fin__gte=eleve.date_inscription).first() if eleve.date_inscription else None
            if year:
                Eleve.objects.filter(id=eleve.id).update(annee_scolaire=year)
                date_updated += 1
        active_updated = 0
        if active_year:
            active_updated = Eleve.objects.filter(annee_scolaire__isnull=True).update(annee_scolaire=active_year)

    print("Association terminee :")
    print(f"- par frais : {fees_updated}")
    print(f"- par date d'inscription : {date_updated}")
    print(f"- annee active : {active_updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
