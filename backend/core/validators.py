# backend/core/validators.py
import os
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validate_file_size(value):
    """ Valide que la taille du fichier ne dépasse pas 10 Mo. """
    limit = 10 * 1024 * 1024  # 10 MB
    if value.size > limit:
        raise ValidationError(_('Le fichier est trop volumineux. La taille ne peut pas dépasser 10 Mo.'))

def validate_file_extension(value):
    """
    Valide que l'extension du fichier est autorisée (images et documents).
    """
    ext = os.path.splitext(value.name)[1].lower()
    valid_extensions = [
        '.jpg', '.jpeg', '.png', '.webp',  # Images
        '.pdf', '.doc', '.docx'             # Documents
    ]
    if not ext in valid_extensions:
        raise ValidationError(_(f'Extension de fichier non supportée. Les extensions autorisées sont : {", ".join(valid_extensions)}'))
