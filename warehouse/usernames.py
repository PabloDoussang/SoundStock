"""Regla compartida para nombres de usuario, incluidos espacios interiores."""
import re
import unicodedata
from django import forms


def normalize_username(value):
    value = unicodedata.normalize('NFKC', value).strip()
    if not value or len(value) > 150 or not re.fullmatch(r'[\w.@+\- ]+', value):
        raise forms.ValidationError('Usa hasta 150 letras, números, espacios o caracteres @ . + - _.')
    return value
