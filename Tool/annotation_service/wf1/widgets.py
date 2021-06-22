from django import forms
from django.utils.safestring import mark_safe


class PlainTextWidget(forms.HiddenInput):
    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(value) if value is not None else '-'
