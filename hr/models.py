from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone

from .holidays import working_days


class Announcement(models.Model):
    title = models.CharField('tytuł', max_length=200)
    body = models.TextField('treść')
    is_pinned = models.BooleanField('przypięte', default=False,
                                    help_text='Przypięte ogłoszenia są wyświetlane na górze.')
    is_published = models.BooleanField('opublikowane', default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='autor', on_delete=models.SET_NULL,
                                   null=True, editable=False, related_name='hr_announcements')
    created_at = models.DateTimeField('utworzono', auto_now_add=True)
    updated_at = models.DateTimeField('zaktualizowano', auto_now=True)

    class Meta:
        verbose_name = 'ogłoszenie HR'
        verbose_name_plural = 'ogłoszenia HR'
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('hr:announcement_detail', args=[self.pk])


class EmployeeProfile(models.Model):
    """Dane kadrowe pracownika, powiązane z kontem użytkownika."""

    class ContractType(models.TextChoices):
        EMPLOYMENT = 'employment', 'Umowa o pracę'
        MANDATE = 'mandate', 'Umowa zlecenie'
        B2B = 'b2b', 'Kontrakt B2B'
        INTERNSHIP = 'internship', 'Staż / praktyki'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name='użytkownik',
                                on_delete=models.CASCADE, related_name='hr_profile')
    phonebook_entry = models.OneToOneField(
        'phonebook.Employee', verbose_name='wpis w książce telefonicznej', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='hr_profile',
        help_text='Z tego wpisu pobierane są wydział, dział, stanowisko, telefon i pokój.',
    )
    employee_number = models.CharField('numer ewidencyjny', max_length=30, blank=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='przełożony', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='subordinate_profiles')
    hire_date = models.DateField('data zatrudnienia', null=True, blank=True)
    contract_type = models.CharField('rodzaj umowy', max_length=20, choices=ContractType.choices,
                                     default=ContractType.EMPLOYMENT)
    working_time = models.DecimalField('wymiar etatu', max_digits=3, decimal_places=2, default=1)
    annual_leave_days = models.PositiveSmallIntegerField('roczny wymiar urlopu (dni)', default=26)
    carried_over_days = models.PositiveSmallIntegerField('urlop zaległy z poprzedniego roku (dni)', default=0)

    class Meta:
        verbose_name = 'profil kadrowy'
        verbose_name_plural = 'profile kadrowe'

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    def leave_used(self, year=None, include_pending=True):
        year = year or timezone.localdate().year
        statuses = [LeaveRequest.Status.APPROVED]
        if include_pending:
            statuses.append(LeaveRequest.Status.PENDING)
        return LeaveRequest.objects.filter(
            user=self.user, start_date__year=year, status__in=statuses,
            leave_type__in=LeaveRequest.COUNTED_TYPES,
        ).aggregate(total=Sum('days'))['total'] or 0

    @property
    def leave_total(self):
        return self.annual_leave_days + self.carried_over_days

    @property
    def leave_remaining(self):
        return self.leave_total - self.leave_used()


class LeaveRequest(models.Model):
    class LeaveType(models.TextChoices):
        ANNUAL = 'annual', 'Urlop wypoczynkowy'
        ON_DEMAND = 'on_demand', 'Urlop na żądanie'
        OCCASIONAL = 'occasional', 'Urlop okolicznościowy'
        CHILDCARE = 'childcare', 'Opieka nad dzieckiem (art. 188 KP)'
        UNPAID = 'unpaid', 'Urlop bezpłatny'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Oczekuje'
        APPROVED = 'approved', 'Zaakceptowany'
        REJECTED = 'rejected', 'Odrzucony'
        CANCELLED = 'cancelled', 'Anulowany'

    # Rodzaje pomniejszające pulę urlopu wypoczynkowego (urlop na żądanie jest jego częścią)
    COUNTED_TYPES = [LeaveType.ANNUAL, LeaveType.ON_DEMAND]
    ON_DEMAND_LIMIT = 4

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='pracownik', on_delete=models.CASCADE,
                             related_name='leave_requests')
    leave_type = models.CharField('rodzaj urlopu', max_length=20, choices=LeaveType.choices,
                                  default=LeaveType.ANNUAL)
    start_date = models.DateField('od')
    end_date = models.DateField('do')
    days = models.PositiveSmallIntegerField('dni robocze', editable=False, default=0)
    note = models.TextField('uwagi', blank=True)
    substitute = models.CharField('zastępstwo', max_length=150, blank=True,
                                  help_text='Kto Cię zastępuje podczas nieobecności.')
    status = models.CharField('status', max_length=20, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='rozpatrzył(a)',
                                    on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='reviewed_leave_requests')
    reviewed_at = models.DateTimeField('data rozpatrzenia', null=True, blank=True)
    review_comment = models.TextField('komentarz HR', blank=True)
    created_at = models.DateTimeField('złożono', auto_now_add=True)

    class Meta:
        verbose_name = 'wniosek urlopowy'
        verbose_name_plural = 'wnioski urlopowe'
        ordering = ['-created_at']
        permissions = [('review_leaverequest', 'Może rozpatrywać wnioski urlopowe')]

    def __str__(self):
        return f'{self.user} — {self.get_leave_type_display()} {self.start_date:%d.%m}–{self.end_date:%d.%m.%Y}'

    def get_absolute_url(self):
        return reverse('hr:leave_detail', args=[self.pk])

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    def save(self, *args, **kwargs):
        self.days = working_days(self.start_date, self.end_date)
        super().save(*args, **kwargs)
