# Photos persistantes avec MinIO sur Railway

Le champ Django `Eleve.photo` reste identique. Les nouvelles photos sont optimisees en WebP puis envoyees automatiquement vers MinIO lorsque `MINIO_ENABLED=true`.

## Variables Railway

Ajoutez ces variables au service Django :

```text
MINIO_ENABLED=true
MINIO_ENDPOINT_URL=https://votre-endpoint-minio
MINIO_ACCESS_KEY=votre-cle-acces
MINIO_SECRET_KEY=votre-cle-secrete
MINIO_BUCKET=sublime-media
MINIO_REGION=us-east-1
```

Le bucket peut rester prive : Django genere des URL presignees temporaires pour
afficher les photos. Par defaut, chaque URL reste valide 1 heure. Vous pouvez
changer cette duree avec `MINIO_URL_EXPIRE_SECONDS` (en secondes). Ne mettez pas
de `/` final dans `MINIO_ENDPOINT_URL`.

## Migration des photos existantes

Avant de retirer le volume contenant `media/`, executez depuis le service Django :

```bash
python manage.py migrate_eleve_photos_to_minio --dry-run
python manage.py migrate_eleve_photos_to_minio
```

La commande recompresse les anciennes photos en WebP, les envoie vers MinIO puis met a jour uniquement leur nom de fichier dans la base de donnees. Les fichiers deja presents dans MinIO sont ignores.
