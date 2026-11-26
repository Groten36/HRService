from django import forms
from django.utils import timezone

from .holidays import working_days
from .models import Announcement, LeaveRequest

DATE = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'body', 'is_pinned', 'is_published']
        widgets = {'body': forms.Textarea(attrs={'rows': 8})}


class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'substitute', 'note']
        widgets = {'start_date': DATE, 'end_date': DATE, 'note': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        start, end, kind = cleaned.get('start_date'), cleaned.get('end_date'), cleaned.get('leave_type')
        if not (start and end and kind):
            return cleaned

        if end < start:
            raise forms.ValidationError('Data końcowa nie może być wcześniejsza niż początkowa.')
        if start.year != end.year:
            raise forms.ValidationError('Wniosek nie może obejmować dwóch lat — złóż dwa osobne wnioski.')
        if start < timezone.localdate() and kind != LeaveRequest.LeaveType.ON_DEMAND:
            self.add_error('start_date', 'Urlop nie może zaczynać się w przeszłości.')

        days = working_days(start, end)
        if days == 0:
            raise forms.ValidationError('Wybrany okres nie zawiera żadnego dnia roboczego.')

        overlapping = LeaveRequest.objects.filter(
            user=self.user, start_date__lte=end, end_date__gte=start,
            status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
        )
        if overlapping.exists():
            raise forms.ValidationError('W tym okresie masz już złożony lub zaakceptowany wniosek.')

        if kind in LeaveRequest.COUNTED_TYPES:
            profile = getattr(self.user, 'hr_profile', None)
            if profile is None:
                raise forms.ValidationError(
                    'Nie masz jeszcze uzupełnionego profilu kadrowego — skontaktuj się z działem HR.')
            remaining = profile.leave_total - profile.leave_used(start.year)
            if days > remaining:
                raise forms.ValidationError(
                    f'Niewystarczająca liczba dni urlopu: wniosek obejmuje {days} dni, pozostało {remaining}.')

        if kind == LeaveRequest.LeaveType.ON_DEMAND:
            used = sum(LeaveRequest.objects.filter(
                user=self.user, leave_type=kind, start_date__year=start.year,
                status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
            ).values_list('days', flat=True))
            if used + days > LeaveRequest.ON_DEMAND_LIMIT:
                raise forms.ValidationError(
                    f'Limit urlopu na żądanie to {LeaveRequest.ON_DEMAND_LIMIT} dni w roku '
                    f'(wykorzystano {used}).')

        cleaned['days'] = days
        return cleaned


class LeaveReviewForm(forms.Form):
    decision = forms.ChoiceField(choices=[
        (LeaveRequest.Status.APPROVED, 'Zaakceptuj'),
        (LeaveRequest.Status.REJECTED, 'Odrzuć'),
    ], widget=forms.HiddenInput)
    comment = forms.CharField(label='Komentarz (opcjonalnie)', required=False,
                              widget=forms.Textarea(attrs={'rows': 2}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('decision') == LeaveRequest.Status.REJECTED and not cleaned.get('comment'):
            self.add_error('comment', 'Podaj powód odrzucenia wniosku.')
        return cleaned


class LeaveFilterForm(forms.Form):
    status = forms.ChoiceField(label='Status', required=False,
                               choices=[('', 'Wszystkie')] + list(LeaveRequest.Status.choices))
    q = forms.CharField(label='Pracownik', required=False,
                        widget=forms.TextInput(attrs={'placeholder': 'Imię, nazwisko lub login'}))
