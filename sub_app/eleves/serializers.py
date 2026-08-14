from django.core.exceptions import ValidationError

from .models import Classe, Eleve, NiveauClasse, Sexe, StatutEleve
from .image_processing import compress_uploaded_photo


def serialize_reference(value):
    if not value:
        return None

    return {
        'code': value.code,
        'libelle': value.libelle,
    }


def serialize_annee_scolaire(annee):
    return {
        'id': annee.id,
        'annee': annee.annee,
        'date_debut': annee.date_debut.isoformat() if annee.date_debut else None,
        'date_fin': annee.date_fin.isoformat() if annee.date_fin else None,
        'est_active': annee.est_active,
    }


def get_annee_scolaire_for_date(date_inscription):
    if not date_inscription:
        return None

    from sub_app.frais_scolaires.models import AnneeScolaire

    return AnneeScolaire.objects.filter(
        date_debut__lte=date_inscription,
        date_fin__gte=date_inscription,
    ).first()


def serialize_classe(classe):
    return {
        'id': classe.id,
        'nom': str(classe),
        'niveau': serialize_reference(classe.niveau),
        'niveau_code': classe.niveau_id,
        'classe_maternel': serialize_reference(classe.classe_maternel),
        'classe_primaire': serialize_reference(classe.classe_primaire),
        'classe_humanite': serialize_reference(classe.classe_humanite),
        'section': serialize_reference(classe.section),
    }


def serialize_eleve(eleve):
    classe = eleve.classe
    annee_scolaire = eleve.annee_scolaire or get_annee_scolaire_for_date(eleve.date_inscription)

    return {
        'id': eleve.id,
        'matricule': eleve.matricule,
        'nom': eleve.nom,
        'post_nom': eleve.post_nom,
        'prenom': eleve.prenom,
        'nom_complet': f'{eleve.nom} {eleve.post_nom} {eleve.prenom}'.strip(),
        'lieu_de_naissance': eleve.lieu_de_naissance,
        'date_naissance': eleve.date_naissance.isoformat() if eleve.date_naissance else None,
        'sexe': eleve.sexe_id,
        'sexe_display': eleve.get_sexe_display(),
        'adresse': eleve.adresse,
        'telephone': eleve.telephone,
        'email': eleve.email,
        'est_masp': eleve.est_masp,
        'classe_id': classe.id if classe else None,
        'classe': str(classe) if classe else '',
        'niveau': str(classe.niveau) if classe else '',
        'niveau_code': classe.niveau_id if classe else '',
        'statut': eleve.statut_id,
        'statut_display': eleve.get_statut_display(),
        'date_inscription': eleve.date_inscription.isoformat() if eleve.date_inscription else None,
        'annee_scolaire_id': annee_scolaire.id if annee_scolaire else None,
        'annee_scolaire': annee_scolaire.annee if annee_scolaire else '',
        'photo_url': eleve.photo.url if eleve.photo else None,
        'created_at': eleve.created_at.isoformat() if eleve.created_at else None,
        'updated_at': eleve.updated_at.isoformat() if eleve.updated_at else None,
    }


def clean_eleve_payload(payload, *, partial=False):
    required_fields = ['nom', 'post_nom', 'prenom', 'sexe', 'statut']
    errors = {}

    if not partial:
        for field in required_fields:
            if not payload.get(field):
                errors[field] = 'Champ requis.'

    data = {}
    text_fields = ['nom', 'post_nom', 'prenom', 'lieu_de_naissance', 'adresse', 'telephone', 'email']
    for field in text_fields:
        if field in payload:
            data[field] = payload.get(field) or ''

    if 'est_masp' in payload:
        value = payload.get('est_masp')
        data['est_masp'] = value if isinstance(value, bool) else str(value).lower() in ['1', 'true', 'on', 'oui']

    if 'date_naissance' in payload:
        data['date_naissance'] = payload.get('date_naissance') or None

    if 'date_inscription' in payload:
        data['date_inscription'] = payload.get('date_inscription') or None

    if not partial:
        from sub_app.frais_scolaires.models import AnneeScolaire

        active_annee = AnneeScolaire.objects.filter(est_active=True).first()
        if active_annee:
            data['annee_scolaire'] = active_annee
        else:
            errors['annee_scolaire'] = "Aucune annee scolaire active n'est configuree."

    if 'classe_id' in payload:
        classe_id = payload.get('classe_id')
        if classe_id:
            try:
                data['classe'] = Classe.objects.get(id=classe_id)
            except Classe.DoesNotExist:
                errors['classe_id'] = 'Classe introuvable.'
        else:
            data['classe'] = None

    if 'sexe' in payload:
        try:
            data['sexe'] = Sexe.objects.get(code=payload.get('sexe'))
        except Sexe.DoesNotExist:
            errors['sexe'] = 'Sexe introuvable.'

    if 'statut' in payload:
        try:
            data['statut'] = StatutEleve.objects.get(code=payload.get('statut'))
        except StatutEleve.DoesNotExist:
            errors['statut'] = 'Statut introuvable.'

    photo = payload.get('photo_file')
    if photo:
        try:
            data['photo'] = compress_uploaded_photo(photo)
        except ValueError as error:
            errors['photo_file'] = str(error)

    if errors:
        raise ValidationError(errors)

    return data
