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


class UsefulLinksTests(TestCase):
    def setUp(self):
        from .models import LinkGroup, UsefulLink
        self.UsefulLink = UsefulLink
        self.gov = LinkGroup.objects.create(name='Urzędy', order=1)
        LinkGroup.objects.create(name='Pusta grupa', order=2)
        UsefulLink.objects.create(group=self.gov, title='ZUS', url='https://www.zus.pl', description='PUE ZUS')
        UsefulLink.objects.create(group=self.gov, title='Ukryty', url='https://example.com', is_active=False)
        UsefulLink.objects.create(title='Telefony', url='/telefony/')

    def test_page_lists_active_links(self):
        response = self.client.get(reverse('pages:links'))
        self.assertContains(response, 'ZUS')
        self.assertContains(response, 'zus.pl')
        self.assertContains(response, 'target="_blank"')
        self.assertContains(response, 'href="/telefony/"')
        self.assertNotContains(response, 'Ukryty')
        self.assertNotContains(response, 'Pusta grupa')

    def test_navbar_and_home_link(self):
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, 'Przydatne linki</a>')

    def test_url_validation(self):
        from django.core.exceptions import ValidationError
        for bad in ('javascript:alert(1)', '//evil.com', 'ftp://x.pl', 'zus.pl'):
            with self.subTest(url=bad), self.assertRaises(ValidationError):
                self.UsefulLink(title='x', url=bad).full_clean()
        for good in ('https://www.zus.pl', 'http://intranet.local/x', '/dokumenty/'):
            with self.subTest(url=good):
                self.UsefulLink(title='x', url=good).full_clean()
