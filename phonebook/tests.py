from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Department, Employee, Section


@override_settings(PHONEBOOK_REQUIRE_LOGIN=False)
class PhonebookTests(TestCase):
    def setUp(self):
        self.it = Department.objects.create(name='Wydział Informatyki')
        self.fin = Department.objects.create(name='Wydział Finansowy')
        self.helpdesk = Section.objects.create(department=self.it, name='Helpdesk')
        self.ksiegowosc = Section.objects.create(department=self.fin, name='Księgowość')
        self.anna = Employee.objects.create(
            first_name='Anna', last_name='Nowak', department=self.it, section=self.helpdesk,
            position='Specjalista IT', phone='22 555 10 20', room='101', email='anna.nowak@example.com',
        )
        self.lukasz = Employee.objects.create(
            first_name='Łukasz', last_name='Żółkiewski', department=self.fin, section=self.ksiegowosc,
            position='Księgowy', phone='+48 22 555 30 40', room='2.15', email='lukasz@example.com',
        )
        self.url = reverse('phonebook:list')

    def names(self, response):
        return {e.last_name for e in response.context['employees']}

    def test_list_shows_all(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.names(response), {'Nowak', 'Żółkiewski'})
        self.assertContains(response, 'href="tel:225551020"')
        self.assertContains(response, 'mailto:anna.nowak@example.com')

    def test_search_polish_case_insensitive(self):
        self.assertEqual(self.names(self.client.get(self.url, {'q': 'łukasz'})), {'Żółkiewski'})
        self.assertEqual(self.names(self.client.get(self.url, {'q': 'ŻÓŁK'})), {'Żółkiewski'})

    def test_search_by_phone_without_spaces(self):
        self.assertEqual(self.names(self.client.get(self.url, {'q': '5551020'})), {'Nowak'})
        self.assertEqual(self.names(self.client.get(self.url, {'q': '555 30'})), {'Żółkiewski'})

    def test_search_multiple_words_and_fields(self):
        self.assertEqual(self.names(self.client.get(self.url, {'q': 'nowak 101'})), {'Nowak'})
        self.assertEqual(self.names(self.client.get(self.url, {'q': 'helpdesk'})), {'Nowak'})
        self.assertEqual(self.names(self.client.get(self.url, {'q': 'nowak księgowy'})), set())

    def test_filters(self):
        self.assertEqual(self.names(self.client.get(self.url, {'department': self.fin.pk})), {'Żółkiewski'})
        self.assertEqual(self.names(self.client.get(self.url, {'section': self.helpdesk.pk})), {'Nowak'})

    def test_section_choices_limited_to_department(self):
        form = self.client.get(self.url, {'department': self.it.pk}).context['form']
        self.assertEqual(list(form.fields['section'].queryset), [self.helpdesk])

    def test_live_search_returns_fragment(self):
        response = self.client.get(self.url, {'q': 'anna'}, HTTP_X_REQUESTED_WITH='fetch')
        self.assertTemplateUsed(response, 'phonebook/_results.html')
        self.assertTemplateNotUsed(response, 'base.html')

    def test_renaming_department_updates_search(self):
        self.it.name = 'Wydział Cyfryzacji'
        self.it.save()
        self.assertEqual(self.names(self.client.get(self.url, {'q': 'cyfryzacji'})), {'Nowak'})

    def test_section_must_belong_to_department(self):
        e = Employee(first_name='X', last_name='Y', department=self.it, section=self.ksiegowosc, phone='1')
        with self.assertRaises(ValidationError):
            e.full_clean()

    def test_invalid_phone(self):
        e = Employee(first_name='X', last_name='Y', department=self.it, phone='abc')
        with self.assertRaises(ValidationError):
            e.full_clean()

    @override_settings(PHONEBOOK_REQUIRE_LOGIN=True)
    def test_requires_login_when_enabled(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_navbar_link(self):
        self.assertContains(self.client.get(reverse('pages:home')), 'Telefony</a>')
