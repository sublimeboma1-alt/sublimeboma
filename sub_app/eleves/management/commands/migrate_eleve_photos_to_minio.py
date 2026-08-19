from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from sub_app.eleves.image_processing import compress_uploaded_photo
from sub_app.eleves.models import Eleve


class Command(BaseCommand):
    help = 'Compresse puis copie les photos locales existantes des eleves vers MinIO.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Affiche les photos a copier sans les envoyer.')

    def handle(self, *args, **options):
        if not settings.MINIO_ENABLED:
            raise CommandError('Activez MINIO_ENABLED=true avant de lancer cette commande.')

        source_storage = FileSystemStorage(location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL)
        copied = skipped = missing = 0
        for eleve in Eleve.objects.exclude(photo='').exclude(photo__isnull=True).iterator():
            name = eleve.photo.name
            if not source_storage.exists(name):
                missing += 1
                self.stderr.write(f'Introuvable localement : {name}')
                continue
            if options['dry_run']:
                copied += 1
                self.stdout.write(f'A compresser et copier : {name}')
                continue
            with source_storage.open(name, 'rb') as source:
                optimized = compress_uploaded_photo(source)
            directory = name.rsplit('/', 1)[0] if '/' in name else 'eleves/photos'
            stem = slugify(name.rsplit('/', 1)[-1].rsplit('.', 1)[0]) or f'eleve-{eleve.id}'
            target_name = f'{directory}/{stem}.webp'
            if default_storage.exists(target_name):
                if eleve.photo.name != target_name:
                    eleve.photo.name = target_name
                    eleve.save(update_fields=['photo', 'updated_at'])
                skipped += 1
                continue
            saved_name = default_storage.save(target_name, optimized)
            eleve.photo.name = saved_name
            eleve.save(update_fields=['photo', 'updated_at'])
            copied += 1

        self.stdout.write(self.style.SUCCESS(
            f'Photos copiees : {copied} | deja presentes : {skipped} | introuvables localement : {missing}'
        ))
