from django import forms

from .models import Department, Section


class EmployeeSearchForm(forms.Form):
    q = forms.CharField(label='Szukaj', required=False, widget=forms.TextInput(attrs={
        'placeholder': 'Imię, nazwisko, numer, pokój, e-mail…', 'autocomplete': 'off', 'autofocus': True,
        'type': 'search',
    }))
    department = forms.ModelChoiceField(label='Wydział', required=False,
                                        queryset=Department.objects.all(), empty_label='Wszystkie')
    section = forms.ModelChoiceField(label='Dział', required=False,
                                     queryset=Section.objects.all(), empty_label='Wszystkie')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['section'].label_from_instance = lambda s: s.name
        dep = self.data.get('department') if self.is_bound else None
        if dep and str(dep).isdigit():
            self.fields['section'].queryset = Section.objects.filter(department_id=dep)
        else:
            self.fields['section'].label_from_instance = str  # „Wydział / Dział”
