"""Regla compartida para nombres de usuario, incluidos espacios interiores."""
import re
import unicodedata
from django import forms
from django.contrib.auth.models import User


def normalize_username(value):
    value = unicodedata.normalize('NFKC', value).strip()
    if not value or len(value) > 150 or not re.fullmatch(r'[\w.@+\- ]+', value):
        raise forms.ValidationError('Usa hasta 150 letras, números, espacios o caracteres @ . + - _.')
    return value


class SpacedUsernameMixin:
    def clean_username(self):
        value = normalize_username(self.cleaned_data['username'])
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ya existe una cuenta con este nombre de usuario.')
        return value

    def _get_validation_exclusions(self):
        # La regla estándar de auth.User no admite espacios. Este formulario
        # aplica arriba su validación y unicidad; la restricción SQL sigue activa.
        excluded = super()._get_validation_exclusions()
        excluded.add('username')
        return excluded
