"""Powiadomienia e-mail dotyczące wniosków urlopowych."""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _send(subject, body, recipients):
    recipients = [r for r in recipients if r]
    if not recipients:
        return
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipients)
    except Exception:  # powiadomienie nie może blokować zapisu wniosku
        logger.exception('Nie udało się wysłać powiadomienia: %s', subject)


def _name(user):
    return user.get_full_name() or user.username


def leave_submitted(request, leave):
    url = request.build_absolute_uri(leave.get_absolute_url())
    _send(
        f'[HR] Nowy wniosek urlopowy — {_name(leave.user)}',
        f'{_name(leave.user)} złożył(a) wniosek: {leave.get_leave_type_display()}\n'
        f'Termin: {leave.start_date:%d.%m.%Y} – {leave.end_date:%d.%m.%Y} ({leave.days} dni roboczych)\n\n'
        f'Rozpatrz wniosek: {url}',
        [settings.HR_EMAIL],
    )


def leave_reviewed(request, leave):
    url = request.build_absolute_uri(leave.get_absolute_url())
    comment = f'\nKomentarz: {leave.review_comment}\n' if leave.review_comment else ''
    _send(
        f'[HR] Twój wniosek urlopowy: {leave.get_status_display().lower()}',
        f'Wniosek: {leave.get_leave_type_display()}, '
        f'{leave.start_date:%d.%m.%Y} – {leave.end_date:%d.%m.%Y}\n'
        f'Status: {leave.get_status_display()}\n{comment}\nSzczegóły: {url}',
        [leave.user.email],
    )
