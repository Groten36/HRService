from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(
    r'^[0-9 +()\-/]+$', 'Numer może zawierać cyfry, spacje oraz znaki + ( ) - /',
)


class Department(models.Model):
    """Wydział."""
    name = models.CharField('nazwa', max_length=150, unique=True)

    class Meta:
        verbose_name = 'wydział'
        verbose_name_plural = 'wydziały'
        ordering = ['name']

    def __str__(self):
        return self.name


class Section(models.Model):
    """Dział — należy do wydziału."""
    department = models.ForeignKey(Department, verbose_name='wydział', on_delete=models.CASCADE,
                                   related_name='sections')
    name = models.CharField('nazwa', max_length=150)

    class Meta:
        verbose_name = 'dział'
        verbose_name_plural = 'działy'
        ordering = ['department__name', 'name']
        constraints = [
            models.UniqueConstraint(fields=['department', 'name'], name='unique_section_per_department'),
        ]

    def __str__(self):
        return f'{self.department} / {self.name}'


class Employee(models.Model):
    first_name = models.CharField('imię', max_length=100)
    last_name = models.CharField('nazwisko', max_length=100)
    department = models.ForeignKey(Department, verbose_name='wydział', on_delete=models.PROTECT,
                                   related_name='employees')
    section = models.ForeignKey(Section, verbose_name='dział', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='employees')
    position = models.CharField('stanowisko', max_length=150, blank=True)
    phone = models.CharField('numer telefonu', max_length=40, validators=[phone_validator])
    room = models.CharField('pokój', max_length=30, blank=True)
    email = models.EmailField('adres e-mail', blank=True)
    # Znormalizowany tekst do wyszukiwania (SQLite nie porównuje polskich znaków bez względu na wielkość liter)
    search_text = models.TextField(editable=False, default='')

    class Meta:
        verbose_name = 'pracownik'
        verbose_name_plural = 'pracownicy'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def phone_href(self):
        return ''.join(c for c in self.phone if c.isdigit() or c == '+')

    def clean(self):
        if self.section_id and self.department_id and self.section.department_id != self.department_id:
            raise ValidationError({'section': 'Wybrany dział nie należy do tego wydziału.'})

    def build_search_text(self):
        parts = [
            self.first_name, self.last_name, f'{self.last_name} {self.first_name}',
            self.position, self.room, self.email, self.phone, self.phone.replace(' ', '').replace('-', ''),
            self.department.name if self.department_id else '',
            self.section.name if self.section_id else '',
        ]
        return ' | '.join(p for p in parts if p).lower()

    def save(self, *args, **kwargs):
        self.search_text = self.build_search_text()
        super().save(*args, **kwargs)
