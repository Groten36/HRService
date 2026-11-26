from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(label='Imię i nazwisko', max_length=100)
    email = forms.EmailField(label='E-mail')
    subject = forms.CharField(label='Temat', max_length=150)
    message = forms.CharField(label='Wiadomość', widget=forms.Textarea(attrs={'rows': 5}))
