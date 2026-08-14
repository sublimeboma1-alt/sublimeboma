from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.text import slugify
from PIL import Image, ImageOps


PHOTO_MAX_SIZE = (900, 900)
PHOTO_QUALITY = 82


def _webp_name(original_name, fallback='photo'):
    stem = Path(original_name or fallback).stem
    safe_stem = slugify(stem) or fallback
    return f'{safe_stem}.webp'


def compress_uploaded_photo(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        image = ImageOps.exif_transpose(image)
        image.thumbnail(PHOTO_MAX_SIZE, Image.Resampling.LANCZOS)

        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')

        output = BytesIO()
        image.save(output, format='WEBP', quality=PHOTO_QUALITY, method=6)
        output.seek(0)
    except Exception as error:
        raise ValueError("La photo n'est pas une image valide.") from error

    return ContentFile(output.read(), name=_webp_name(uploaded_file.name))


def compress_existing_photo_field(photo_field):
    if not photo_field:
        return None

    old_name = photo_field.name
    if not default_storage.exists(old_name):
        return None

    with photo_field.open('rb') as source:
        optimized = compress_uploaded_photo(source)

    directory = str(Path(old_name).parent).replace('\\', '/')
    new_name = f'{directory}/{_webp_name(old_name)}' if directory != '.' else _webp_name(old_name)
    saved_name = default_storage.save(new_name, optimized)

    return saved_name
