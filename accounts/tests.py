from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountsTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('signup'), {
            'username': 'nowy',
            'email': 'nowy@example.com',
            'password1': 'BardzoTrudneHaslo123!',
            'password2': 'BardzoTrudneHaslo123!',
        })
        self.assertRedirects(response, reverse('pages:home'))
        self.assertTrue(User.objects.filter(username='nowy').exists())
        self.assertIn('_auth_user_id', self.client.session)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_login_page_renders(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
