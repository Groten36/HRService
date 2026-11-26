import os

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .models import ALLOWED_EXTENSIONS, DOCUMENT_EXTENSIONS, SOFTWARE_EXTENSIONS, Category, Document


def rules_for(kind):
    """Dozwolone rozszerzenia i limit rozmiaru (MB) dla danego rodzaju."""
    if kind == Document.Kind.SOFTWARE:
        return SOFTWARE_EXTENSIONS, settings.SOFTWARE_MAX_UPLOAD_MB
    return DOCUMENT_EXTENSIONS, settings.DOCUMENT_MAX_UPLOAD_MB


class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'kind', 'number', 'category', 'description', 'file',
                  'effective_date', 'is_published']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'effective_date': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'file': forms.ClearableFileInput(attrs={
                'accept': ','.join(f'.{e}' for e in ALLOWED_EXTENSIONS),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].help_text = (
            f"Dokumenty: {', '.join(DOCUMENT_EXTENSIONS)} (maks. {settings.DOCUMENT_MAX_UPLOAD_MB} MB). "
            f"Programy: {', '.join(SOFTWARE_EXTENSIONS)} (maks. {settings.SOFTWARE_MAX_UPLOAD_MB} MB)."
        )

    def clean(self):
        cleaned = super().clean()
        kind, f = cleaned.get('kind'), cleaned.get('file')
        if not kind or not f:
            return cleaned
        extensions, max_mb = rules_for(kind)
        ext = os.path.splitext(f.name)[1].lstrip('.').lower()
        if ext not in extensions:
            self.add_error('file', f"Dla rodzaju „{Document.Kind(kind).label}” dozwolone są: {', '.join(extensions)}.")
        elif isinstance(f, UploadedFile) and f.size > max_mb * 1024 * 1024:
            self.add_error('file', f'Plik jest za duży (maks. {max_mb} MB).')
        return cleaned


class DocumentFilterForm(forms.Form):
    q = forms.CharField(label='Szukaj', required=False,
                        widget=forms.TextInput(attrs={'placeholder': 'Tytuł, numer, opis…'}))
    kind = forms.ChoiceField(label='Rodzaj', required=False,
                             choices=[('', 'Wszystkie')] + list(Document.Kind.choices))
    category = forms.ModelChoiceField(label='Kategoria', required=False,
                                      queryset=Category.objects.all(), empty_label='Wszystkie')
