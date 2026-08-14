from django.core.management.base import BaseCommand

from sub_app.eleves.image_processing import compress_existing_photo_field
from sub_app.eleves.models import Eleve


class Command(BaseCommand):
    help = 'Compresse les photos des eleves en WebP leger.'

    def handle(self, *args, **options):
        updated = 0
        skipped = 0

        for eleve in Eleve.objects.exclude(photo='').exclude(photo__isnull=True):
            old_name = eleve.photo.name
            try:
                new_name = compress_existing_photo_field(eleve.photo)
            except ValueError:
                skipped += 1
                continue

            if new_name and new_name != old_name:
                eleve.photo.name = new_name
                eleve.save(update_fields=['photo', 'updated_at'])
                updated += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f'Photos compressees: {updated}; ignorees: {skipped}.'))
