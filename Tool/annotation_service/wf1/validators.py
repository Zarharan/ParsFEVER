from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def line_count_validator(value):
    line_count = len(value.splitlines())
    if line_count < 2 or line_count > 5:
        raise ValidationError(
            _('Enter 2-5 claims'),
            params={'value': value},
        )
