from django import forms
from django.contrib.auth.forms import SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User

from .roles import ROLE_CHOICES, get_role


class UserCreateForm(UserCreationForm):
    role = forms.ChoiceField(label='Rola', choices=ROLE_CHOICES, initial='employee')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True


class UserUpdateForm(forms.ModelForm):
    role = forms.ChoiceField(label='Rola', choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'is_active')
        help_texts = {'is_active': 'Odznacz, aby zablokować logowanie bez usuwania konta.'}

    def __init__(self, *args, editor, **kwargs):
        super().__init__(*args, **kwargs)
        role = get_role(self.instance)
        self.fields['role'].initial = role.key if role else 'employee'
        self.fields['email'].required = True
        if self.instance == editor:
            # Nie można odebrać sobie roli ani zablokować własnego konta
            for name in ('role', 'is_active'):
                self.fields[name].disabled = True
                self.fields[name].help_text = 'Nie możesz zmienić tego we własnym koncie.'


class AdminSetPasswordForm(SetPasswordForm):
    pass


class UserFilterForm(forms.Form):
    q = forms.CharField(label='Szukaj', required=False,
                        widget=forms.TextInput(attrs={'placeholder': 'Login, imię, nazwisko, e-mail'}))
    role = forms.ChoiceField(label='Rola', required=False, choices=[('', 'Wszystkie')] + ROLE_CHOICES)
