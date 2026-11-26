from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db import models


def validate_link_url(value):
    """Dozwolone: adresy http(s) albo ścieżki wewnętrzne zaczynające się od '/'."""
    if value.startswith('/') and not value.startswith('//'):
        return
    parsed = urlparse(value)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValidationError('Podaj pełny adres (https://…) lub ścieżkę wewnętrzną zaczynającą się od „/”.')


class LinkGroup(models.Model):
    name = models.CharField('nazwa', max_length=100, unique=True)
    order = models.PositiveSmallIntegerField('kolejność', default=0)

    class Meta:
        verbose_name = 'grupa linków'
        verbose_name_plural = 'grupy linków'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class UsefulLink(models.Model):
    group = models.ForeignKey(LinkGroup, verbose_name='grupa', on_delete=models.SET_NULL,
                              null=True, blank=True, related_name='links')
    title = models.CharField('nazwa', max_length=150)
    url = models.CharField('adres', max_length=500, validators=[validate_link_url],
                           help_text='Np. https://www.zus.pl albo /telefony/')
    description = models.CharField('opis', max_length=255, blank=True)
    order = models.PositiveSmallIntegerField('kolejność', default=0)
    is_active = models.BooleanField('widoczny', default=True)

    class Meta:
        verbose_name = 'przydatny link'
        verbose_name_plural = 'przydatne linki'
        ordering = ['order', 'title']

    def __str__(self):
        return self.title

    @property
    def is_external(self):
        return not self.url.startswith('/')

    @property
    def domain(self):
        return urlparse(self.url).netloc.removeprefix('www.') if self.is_external else ''
