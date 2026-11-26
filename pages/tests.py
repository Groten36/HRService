from django.core import mail
from django.test import TestCase
from django.urls import reverse


class PagesTests(TestCase):
    def test_static_pages_render(self):
        for name in ('pages:home', 'pages:about', 'pages:contact'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_contact_form_sends_email(self):
        response = self.client.post(reverse('pages:contact'), {
            'name': 'Jan Kowalski',
            'email': 'jan@example.com',
            'subject': 'Pytanie',
            'message': 'Treść wiadomości',
        }, follow=True)
        self.assertRedirects(response, reverse('pages:contact'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Pytanie', mail.outbox[0].subject)
