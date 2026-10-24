import io
import warnings

from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError

from events.security import DomainError

Image.MAX_IMAGE_PIXELS = 40_000_000


def normalize(upload):
    if upload.size > settings.UPLOAD_MAX_BYTES:
        raise DomainError("Zdjęcie przekracza 15 MiB.", 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise DomainError(
                        "Wybierz JPEG, PNG lub WebP. HEIC najpierw przekonwertuj.", 400
                    )
                expected = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[
                    source.format
                ]
                if getattr(upload, "content_type", expected) != expected:
                    raise DomainError("Typ pliku nie odpowiada jego zawartości.", 400)
                if source.width * source.height > 40_000_000 or getattr(source, "n_frames", 1) != 1:
                    raise DomainError("Maksymalnie 40 megapikseli, bez animacji.", 413)
                source.load()
                oriented = ImageOps.exif_transpose(source)
                oriented.thumbnail((1920, 1920))
                # New image strips all EXIF, GPS, ICC, comments and source metadata.
                clean = Image.new("RGB", oriented.size, "white")
                if "A" in oriented.getbands():
                    clean.paste(oriented.convert("RGB"), mask=oriented.getchannel("A"))
                else:
                    clean.paste(oriented.convert("RGB"))
            for quality in (88, 78, 65, 50, 40):
                output = io.BytesIO()
                clean.save(output, "JPEG", quality=quality, optimize=True)
                if output.tell() <= settings.PHOTO_MAX_BYTES:
                    return output.getvalue()
                clean.thumbnail((int(clean.width * 0.85), int(clean.height * 0.85)))
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ):
        raise DomainError("Nie można odczytać obrazu lub przekracza on limit pikseli.", 400)
    raise DomainError("Nie udało się zmniejszyć zdjęcia do 1 MiB.", 413)
