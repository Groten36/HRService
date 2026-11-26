from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from .roles import EMPLOYEE, HR_ADMIN, IT_ADMIN, get_role, set_role


def make_user(username, role=None, **kw):
    user = User.objects.create_user(username, password='TrudneHaslo123!', email=f'{username}@example.com', **kw)
    if role:
        set_role(user, role.key)
    return user


class AccountsTests(TestCase):
    def test_public_signup_is_disabled(self):
        response = self.client.get('/accounts/rejestracja/')
        self.assertEqual(response.status_code, 404)
        self.assertNotContains(self.client.get(reverse('login')), 'rejestracja')

    def test_new_user_created_by_it_defaults_to_employee(self):
        it = make_user('it', IT_ADMIN)
        self.client.force_login(it)
        self.assertContains(self.client.get(reverse('user_create')), '<option value="employee" selected>')

    def test_superuser_can_create_users(self):
        root = User.objects.create_superuser('root', 'root@example.com', 'x')
        self.client.force_login(root)
        response = self.client.post(reverse('user_create'), {
            'username': 'nowy', 'email': 'nowy@example.com', 'role': 'employee',
            'password1': 'BardzoTrudneHaslo123!', 'password2': 'BardzoTrudneHaslo123!',
        })
        self.assertRedirects(response, reverse('user_list'))
        self.assertEqual(get_role(User.objects.get(username='nowy')), EMPLOYEE)

    def test_hr_and_employee_cannot_create_users(self):
        for role in (EMPLOYEE, HR_ADMIN):
            self.client.force_login(make_user(f'u_{role.key}', role))
            response = self.client.post(reverse('user_create'), {
                'username': 'intruz', 'email': 'i@example.com', 'role': 'it_admin',
                'password1': 'BardzoTrudneHaslo123!', 'password2': 'BardzoTrudneHaslo123!',
            })
            self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='intruz').exists())

    def test_profile_requires_login(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_login_page_renders(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)


class RoleSetupTests(TestCase):
    def test_groups_created_by_migrate(self):
        for role in (EMPLOYEE, IT_ADMIN, HR_ADMIN):
            self.assertTrue(Group.objects.filter(name=role.name).exists())

    def test_set_role_switches_group_and_staff(self):
        user = make_user('x', EMPLOYEE)
        set_role(user, IT_ADMIN.key)
        self.assertEqual(get_role(user), IT_ADMIN)
        self.assertTrue(user.is_staff)
        self.assertEqual(user.groups.count(), 1)
        set_role(user, EMPLOYEE.key)
        user.refresh_from_db()
        self.assertFalse(user.is_staff)


class PermissionMatrixTests(TestCase):
    """Kto co może — zgodnie z definicją ról."""

    def setUp(self):
        self.employee = make_user('pracownik', EMPLOYEE)
        self.it = make_user('it', IT_ADMIN)
        self.hr = make_user('hr', HR_ADMIN)

    def check(self, user, perm, expected):
        user = User.objects.get(pk=user.pk)  # świeży cache uprawnień
        self.assertEqual(user.has_perm(perm), expected, f'{user.username} / {perm}')

    def test_employee_has_no_management_perms(self):
        for perm in ('auth.add_user', 'documents.add_document', 'pages.add_usefullink',
                     'hr.add_announcement', 'hr.review_leaverequest', 'phonebook.add_employee'):
            self.check(self.employee, perm, False)

    def test_it_admin(self):
        for perm in ('auth.add_user', 'auth.change_user', 'auth.delete_user',
                     'documents.add_document', 'documents.delete_document', 'documents.add_category',
                     'pages.add_usefullink', 'pages.change_linkgroup'):
            self.check(self.it, perm, True)
        for perm in ('hr.add_announcement', 'hr.review_leaverequest', 'phonebook.add_employee'):
            self.check(self.it, perm, False)

    def test_hr_admin(self):
        for perm in ('hr.add_announcement', 'hr.delete_announcement', 'hr.review_leaverequest',
                     'hr.change_employeeprofile', 'phonebook.add_employee', 'phonebook.change_department'):
            self.check(self.hr, perm, True)
        for perm in ('auth.add_user', 'auth.change_user', 'documents.add_document', 'pages.add_usefullink'):
            self.check(self.hr, perm, False)

    def test_pages_access(self):
        cases = {
            reverse('user_list'): {'pracownik': 403, 'it': 200, 'hr': 200},  # HR: podgląd (view_user)
            reverse('user_create'): {'pracownik': 403, 'it': 200, 'hr': 403},
            reverse('documents:create'): {'pracownik': 403, 'it': 200, 'hr': 403},
            reverse('hr:announcement_create'): {'pracownik': 403, 'it': 403, 'hr': 200},
            reverse('hr:leave_review'): {'pracownik': 403, 'it': 403, 'hr': 200},
            reverse('hr:leave_create'): {'pracownik': 200, 'it': 200, 'hr': 200},
            reverse('hr:announcements'): {'pracownik': 200, 'it': 200, 'hr': 200},
        }
        for user in (self.employee, self.it, self.hr):
            self.client.force_login(user)
            for url, expected in cases.items():
                with self.subTest(user=user.username, url=url):
                    self.assertEqual(self.client.get(url).status_code, expected[user.username])


class UserManagementTests(TestCase):
    def setUp(self):
        self.it = make_user('it', IT_ADMIN)
        self.employee = make_user('jan', EMPLOYEE, first_name='Jan')
        self.root = User.objects.create_superuser('root', 'root@example.com', 'x')
        self.client.force_login(self.it)

    def test_create_user_with_role(self):
        response = self.client.post(reverse('user_create'), {
            'username': 'kadrowa', 'first_name': 'Ewa', 'last_name': 'K', 'email': 'ewa@example.com',
            'role': 'hr_admin', 'password1': 'BardzoTrudneHaslo123!', 'password2': 'BardzoTrudneHaslo123!',
        })
        self.assertRedirects(response, reverse('user_list'))
        user = User.objects.get(username='kadrowa')
        self.assertEqual(get_role(user), HR_ADMIN)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_change_role_and_block(self):
        self.client.post(reverse('user_update', args=[self.employee.pk]), {
            'username': 'jan', 'first_name': 'Jan', 'last_name': 'Nowak', 'email': 'jan@example.com',
            'role': 'it_admin',
        })
        self.employee.refresh_from_db()
        self.assertEqual(get_role(self.employee), IT_ADMIN)
        self.assertEqual(self.employee.last_name, 'Nowak')
        self.assertFalse(self.employee.is_active)  # checkbox nie zaznaczony

    def test_set_password(self):
        self.client.post(reverse('user_password', args=[self.employee.pk]), {
            'new_password1': 'NoweHaslo!2026xyz', 'new_password2': 'NoweHaslo!2026xyz',
        })
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.check_password('NoweHaslo!2026xyz'))

    def test_delete_user(self):
        response = self.client.post(reverse('user_delete', args=[self.employee.pk]))
        self.assertRedirects(response, reverse('user_list'))
        self.assertFalse(User.objects.filter(username='jan').exists())

    def test_cannot_touch_superuser(self):
        for name in ('user_update', 'user_password', 'user_delete'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name, args=[self.root.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('user_delete', args=[self.root.pk])).status_code, 403)
        self.assertTrue(User.objects.filter(username='root').exists())

    def test_cannot_delete_self_or_change_own_role(self):
        self.assertEqual(self.client.post(reverse('user_delete', args=[self.it.pk])).status_code, 403)
        self.client.post(reverse('user_update', args=[self.it.pk]), {
            'username': 'it', 'email': 'it@example.com', 'role': 'employee',
        })
        self.it.refresh_from_db()
        self.assertEqual(get_role(self.it), IT_ADMIN)
        self.assertTrue(self.it.is_active)

    def test_admin_hides_superuser_fields_for_it(self):
        response = self.client.get(reverse('admin:auth_user_change', args=[self.employee.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="is_superuser"')
        self.assertNotContains(response, 'name="user_permissions"')
        # Tylko grupy ról do wyboru
        self.assertEqual(
            set(response.context['adminform'].form.fields['groups'].queryset.values_list('name', flat=True)),
            {'Pracownik', 'Administrator IT', 'Administrator HR'})

    def test_admin_blocks_editing_superuser(self):
        response = self.client.post(reverse('admin:auth_user_change', args=[self.root.pk]),
                                    {'username': 'root', 'is_superuser': 'on'})
        self.assertIn(response.status_code, (302, 403))
        self.root.refresh_from_db()
        self.assertEqual(self.root.username, 'root')
        response = self.client.post(reverse('admin:auth_user_delete', args=[self.root.pk]), {'post': 'yes'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.filter(pk=self.root.pk).exists())

    def test_it_cannot_grant_superuser_via_admin(self):
        self.client.post(reverse('admin:auth_user_change', args=[self.employee.pk]), {
            'username': 'jan', 'email': 'jan@example.com', 'is_active': 'on', 'is_superuser': 'on',
            'date_joined_0': '2026-01-01', 'date_joined_1': '10:00:00',
            'hr_profile-TOTAL_FORMS': '0', 'hr_profile-INITIAL_FORMS': '0',
        })
        self.employee.refresh_from_db()
        self.assertFalse(self.employee.is_superuser)
