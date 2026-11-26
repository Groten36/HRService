import shutil
import tempfile

from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Category, Document

MEDIA = tempfile.mkdtemp()


def pdf(name='zarzadzenie.pdf', content=b'%PDF-1.4 test'):
    return SimpleUploadedFile(name, content, content_type='application/pdf')


@override_settings(MEDIA_ROOT=MEDIA)
class DocumentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user('pracownik', password='haslo12345!')
        self.editor = User.objects.create_user('redaktor', password='haslo12345!')
        self.editor.user_permissions.set(Permission.objects.filter(
            codename__in=['add_document', 'change_document', 'delete_document']))
        self.category = Category.objects.create(name='BHP')
        self.doc = Document.objects.create(
            title='Zarządzenie BHP', kind=Document.Kind.ORDER, number='1/2026',
            category=self.category, file=pdf(), original_filename='zarzadzenie.pdf',
        )
        self.draft = Document.objects.create(
            title='Szkic porady', kind=Document.Kind.ADVICE, file=pdf('szkic.pdf'),
            original_filename='szkic.pdf', is_published=False,
        )

    @override_settings(DOCUMENTS_REQUIRE_LOGIN=True)
    def test_list_requires_login_when_enabled(self):
        for url in (reverse('documents:list'), reverse('documents:detail', args=[self.doc.pk]),
                    reverse('documents:download', args=[self.doc.pk])):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    @override_settings(DOCUMENTS_REQUIRE_LOGIN=False)
    def test_anonymous_access_when_login_not_required(self):
        response = self.client.get(reverse('documents:list'))
        self.assertContains(response, 'Zarządzenie BHP')
        self.assertNotContains(response, 'Szkic porady')
        self.assertEqual(self.client.get(reverse('documents:download', args=[self.doc.pk])).status_code, 200)
        # Edycja nadal wymaga uprawnień
        self.assertEqual(self.client.get(reverse('documents:create')).status_code, 302)

    def test_employee_sees_only_published(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse('documents:list'))
        self.assertContains(response, 'Zarządzenie BHP')
        self.assertNotContains(response, 'Szkic porady')
        self.assertEqual(self.client.get(reverse('documents:detail', args=[self.draft.pk])).status_code, 404)

    def test_editor_sees_drafts(self):
        self.client.force_login(self.editor)
        self.assertContains(self.client.get(reverse('documents:list')), 'Szkic porady')

    def test_filters(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse('documents:list'), {'kind': 'advice'})
        self.assertContains(response, 'Szkic porady')
        self.assertNotContains(response, 'Zarządzenie BHP')
        response = self.client.get(reverse('documents:list'), {'q': '1/2026'})
        self.assertContains(response, 'Zarządzenie BHP')

    def test_download_uses_original_filename(self):
        self.client.force_login(self.employee)
        response = self.client.get(reverse('documents:download', args=[self.doc.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('zarzadzenie.pdf', response['Content-Disposition'])
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-1.4 test')

    def test_employee_cannot_create(self):
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get(reverse('documents:create')).status_code, 403)

    def test_editor_can_create(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('documents:create'), {
            'title': 'Nowa porada', 'kind': 'advice', 'file': pdf('porada.pdf'),
            'is_published': 'on',
        })
        doc = Document.objects.get(title='Nowa porada')
        self.assertRedirects(response, doc.get_absolute_url())
        self.assertEqual(doc.original_filename, 'porada.pdf')
        self.assertEqual(doc.uploaded_by, self.editor)
        self.assertNotIn('porada', doc.file.name)  # losowa nazwa na dysku

    def test_rejects_disallowed_extension(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('documents:create'), {
            'title': 'Zły plik', 'kind': 'order',
            'file': SimpleUploadedFile('skrypt.exe', b'MZ'),
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Document.objects.filter(title='Zły plik').exists())

    @override_settings(DOCUMENT_MAX_UPLOAD_MB=0)
    def test_rejects_too_large_file(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('documents:create'), {
            'title': 'Duży', 'kind': 'order', 'file': pdf(),
        })
        self.assertContains(response, 'za duży')

    def test_delete_removes_file(self):
        self.client.force_login(self.editor)
        storage, name = self.doc.file.storage, self.doc.file.name
        self.assertTrue(storage.exists(name))
        response = self.client.post(reverse('documents:delete', args=[self.doc.pk]))
        self.assertRedirects(response, reverse('documents:list'))
        self.assertFalse(storage.exists(name))

    def test_replacing_file_removes_old_one(self):
        self.client.force_login(self.editor)
        storage, old = self.doc.file.storage, self.doc.file.name
        self.client.post(reverse('documents:update', args=[self.doc.pk]), {
            'title': self.doc.title, 'kind': 'order', 'file': pdf('nowy.pdf'),
            'is_published': 'on',
        })
        self.doc.refresh_from_db()
        self.assertFalse(storage.exists(old))
        self.assertEqual(self.doc.original_filename, 'nowy.pdf')


@override_settings(MEDIA_ROOT=MEDIA, DOCUMENTS_REQUIRE_LOGIN=False)
class CategoryNavTests(TestCase):
    def setUp(self):
        self.bhp = Category.objects.create(name='BHP')
        self.kadry = Category.objects.create(name='Kadry i płace')
        Document.objects.create(title='Dok BHP', category=self.bhp, file=pdf(), original_filename='a.pdf')
        Document.objects.create(title='Dok kadry', category=self.kadry, file=pdf(), original_filename='b.pdf')

    def test_polish_slug(self):
        self.assertEqual(self.kadry.slug, 'kadry-i-place')

    def test_navbar_lists_categories(self):
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, reverse('documents:category', args=['bhp']))
        self.assertContains(response, reverse('documents:category', args=['kadry-i-place']))

    def test_category_page_filters(self):
        response = self.client.get(reverse('documents:category', args=['bhp']))
        self.assertContains(response, 'Dok BHP')
        self.assertNotContains(response, 'Dok kadry')

    def test_unknown_category_404(self):
        self.assertEqual(self.client.get(reverse('documents:category', args=['brak'])).status_code, 404)


@override_settings(MEDIA_ROOT=MEDIA, DOCUMENTS_REQUIRE_LOGIN=False)
class SoftwarePageTests(TestCase):
    def setUp(self):
        Document.objects.create(title='Klient VPN', kind=Document.Kind.SOFTWARE, number='5.2',
                                file=SimpleUploadedFile('vpn.msi', b'MSI'), original_filename='vpn.msi')
        Document.objects.create(title='Zarządzenie X', kind=Document.Kind.ORDER,
                                file=pdf(), original_filename='z.pdf')
        self.editor = User.objects.create_user('redaktor', password='haslo12345!')
        self.editor.user_permissions.set(Permission.objects.filter(codename='add_document'))

    def test_software_page_shows_only_programs(self):
        response = self.client.get(reverse('documents:software'))
        self.assertContains(response, 'Klient VPN')
        self.assertContains(response, 'wersja 5.2')
        self.assertNotContains(response, 'Zarządzenie X')

    def test_navbar_has_programs_link(self):
        response = self.client.get(reverse('pages:home'))
        self.assertContains(response, reverse('documents:software'))
        self.assertContains(response, '>Programy</a>')

    def test_installer_download_is_attachment(self):
        doc = Document.objects.get(title='Klient VPN')
        response = self.client.get(reverse('documents:download', args=[doc.pk]) + '?inline=1')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('vpn.msi', response['Content-Disposition'])

    def test_editor_can_upload_installer(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('documents:create'), {
            'title': 'Edytor PDF', 'kind': 'software', 'number': '1.0',
            'file': SimpleUploadedFile('setup.exe', b'MZ'), 'is_published': 'on',
        })
        doc = Document.objects.get(title='Edytor PDF')
        self.assertRedirects(response, doc.get_absolute_url())
        self.assertEqual(doc.original_filename, 'setup.exe')

    def test_installer_rejected_as_document(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('documents:create'), {
            'title': 'Zły', 'kind': 'order', 'file': SimpleUploadedFile('setup.exe', b'MZ'),
        })
        self.assertContains(response, 'dozwolone są')
        self.assertFalse(Document.objects.filter(title='Zły').exists())

    def test_pdf_rejected_as_program(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('documents:create'), {
            'title': 'Zły', 'kind': 'software', 'file': pdf(),
        })
        self.assertContains(response, 'dozwolone są')

    @override_settings(SOFTWARE_MAX_UPLOAD_MB=0)
    def test_program_size_limit(self):
        self.client.force_login(self.editor)
        response = self.client.post(reverse('documents:create'), {
            'title': 'Duży', 'kind': 'software', 'file': SimpleUploadedFile('a.zip', b'PK'),
        })
        self.assertContains(response, 'za duży')

    def test_create_preselects_kind(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse('documents:create') + '?kind=software')
        self.assertContains(response, '<option value="software" selected>')
