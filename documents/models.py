import os
import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

DOCUMENT_EXTENSIONS = ['pdf', 'doc', 'docx', 'odt', 'xls', 'xlsx', 'ods', 'txt', 'png', 'jpg', 'jpeg']
SOFTWARE_EXTENSIONS = ['exe', 'msi', 'msix', 'zip', '7z', 'dmg', 'pkg', 'deb', 'rpm', 'appimage']
ALLOWED_EXTENSIONS = DOCUMENT_EXTENSIONS + SOFTWARE_EXTENSIONS


def document_upload_to(instance, filename):
    """Pliki zapisywane pod losową nazwą — oryginalna nazwa trafia do bazy."""
    ext = os.path.splitext(filename)[1].lower()
    return f'documents/{uuid.uuid4().hex}{ext}'


class Category(models.Model):
    name = models.CharField('nazwa', max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)

    class Meta:
        verbose_name = 'kategoria'
        verbose_name_plural = 'kategorie'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name.replace('ł', 'l').replace('Ł', 'L'))
        super().save(*args, **kwargs)


class Document(models.Model):
    class Kind(models.TextChoices):
        ORDER = 'order', 'Zarządzenie'
        ADVICE = 'advice', 'Porada'
        SOFTWARE = 'software', 'Program'

    title = models.CharField('tytuł', max_length=200)
    kind = models.CharField('rodzaj', max_length=10, choices=Kind.choices, default=Kind.ORDER)
    number = models.CharField(
        'numer / wersja', max_length=50, blank=True,
        help_text='Np. numer zarządzenia (12/2026) lub wersja programu (2.4.1)',
    )
    category = models.ForeignKey(
        Category, verbose_name='kategoria', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents',
    )
    description = models.TextField('opis', blank=True)
    file = models.FileField(
        'plik', upload_to=document_upload_to,
        validators=[FileExtensionValidator(ALLOWED_EXTENSIONS)],
    )
    original_filename = models.CharField(max_length=255, editable=False)
    effective_date = models.DateField('obowiązuje od', null=True, blank=True)
    is_published = models.BooleanField('opublikowany', default=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name='dodał(a)', on_delete=models.SET_NULL,
        null=True, editable=False, related_name='documents',
    )
    created_at = models.DateTimeField('utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('zaktualizowano', auto_now=True)

    class Meta:
        verbose_name = 'dokument'
        verbose_name_plural = 'dokumenty'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('documents:detail', args=[self.pk])

    @property
    def extension(self):
        return os.path.splitext(self.original_filename or self.file.name)[1].lstrip('.').upper()

    @property
    def size(self):
        try:
            return self.file.size
        except (FileNotFoundError, ValueError):
            return None
