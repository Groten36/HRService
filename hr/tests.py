from datetime import date, timedelta

from django.contrib.auth.models import Permission, User
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .holidays import easter_sunday, polish_holidays, working_days
from .models import Announcement, EmployeeProfile, LeaveRequest


def next_monday(weeks_ahead=2):
    """Poniedziałek w przyszłości, bez świąt w danym tygodniu."""
    d = timezone.localdate() + timedelta(weeks=weeks_ahead)
    d -= timedelta(days=d.weekday())
    while any((d + timedelta(days=i)) in polish_holidays(d.year) for i in range(5)) or d.year != (d + timedelta(days=4)).year:
        d += timedelta(weeks=1)
    return d


class HolidayTests(TestCase):
    def test_easter(self):
        self.assertEqual(easter_sunday(2026), date(2026, 4, 5))
        self.assertEqual(easter_sunday(2027), date(2027, 3, 28))

    def test_working_days_skip_weekends_and_holidays(self):
        # 2026-04-30 (czw) .. 2026-05-06 (śr): 1 i 3 maja święta, weekend 2-3
        self.assertEqual(working_days(date(2026, 4, 30), date(2026, 5, 6)), 4)
        self.assertEqual(working_days(date(2026, 12, 21), date(2026, 12, 27)), 3)  # Wigilia i święta
        self.assertEqual(working_days(date(2026, 5, 2), date(2026, 5, 3)), 0)


class HRBase(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user('jan', password='x', first_name='Jan', last_name='Kowalski',
                                                 email='jan@example.com')
        self.profile = EmployeeProfile.objects.create(user=self.employee, annual_leave_days=20, carried_over_days=2)
        self.hr = User.objects.create_user('kadry', password='x', first_name='Ewa', last_name='Kadrowa')
        self.hr.user_permissions.set(Permission.objects.filter(
            content_type__app_label='hr',
            codename__in=['review_leaverequest', 'add_announcement', 'change_announcement', 'delete_announcement']))
        self.monday = next_monday()

    def leave(self, user=None, start=None, days=5, **kw):
        start = start or self.monday
        return LeaveRequest.objects.create(user=user or self.employee, start_date=start,
                                           end_date=start + timedelta(days=days - 1), **kw)


class AccessTests(HRBase):
    def test_all_pages_require_login(self):
        for name in ('hr:dashboard', 'hr:announcements', 'hr:my_profile', 'hr:leave_list',
                     'hr:leave_create', 'hr:leave_review'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response.url)

    def test_employee_pages(self):
        self.client.force_login(self.employee)
        for name in ('hr:dashboard', 'hr:announcements', 'hr:my_profile', 'hr:leave_list', 'hr:leave_create'):
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_employee_cannot_review_or_manage_announcements(self):
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get(reverse('hr:leave_review')).status_code, 403)
        self.assertEqual(self.client.get(reverse('hr:announcement_create')).status_code, 403)
        self.assertNotContains(self.client.get(reverse('hr:dashboard')), 'Wnioski do rozpatrzenia')

    def test_user_without_profile(self):
        other = User.objects.create_user('bez', password='x')
        self.client.force_login(other)
        self.assertContains(self.client.get(reverse('hr:my_profile')), 'nie został jeszcze uzupełniony')

    def test_cannot_see_others_leave(self):
        leave = self.leave()
        other = User.objects.create_user('inny', password='x')
        self.client.force_login(other)
        self.assertEqual(self.client.get(leave.get_absolute_url()).status_code, 404)


class LeaveRequestTests(HRBase):
    def post_leave(self, start, end, kind='annual'):
        return self.client.post(reverse('hr:leave_create'), {
            'leave_type': kind, 'start_date': start.isoformat(), 'end_date': end.isoformat(),
        })

    def test_submit_counts_working_days_and_notifies_hr(self):
        self.client.force_login(self.employee)
        response = self.post_leave(self.monday, self.monday + timedelta(days=6))  # pn–nd
        leave = LeaveRequest.objects.get()
        self.assertRedirects(response, leave.get_absolute_url())
        self.assertEqual(leave.days, 5)
        self.assertEqual(leave.status, LeaveRequest.Status.PENDING)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Nowy wniosek', mail.outbox[0].subject)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.leave_remaining, 22 - 5)

    def test_rejects_end_before_start(self):
        self.client.force_login(self.employee)
        response = self.post_leave(self.monday, self.monday - timedelta(days=1))
        self.assertContains(response, 'nie może być wcześniejsza')

    def test_rejects_past_dates(self):
        self.client.force_login(self.employee)
        past = timezone.localdate() - timedelta(days=30)
        self.assertContains(self.post_leave(past, past + timedelta(days=1)), 'w przeszłości')

    def test_rejects_overlap(self):
        self.leave()
        self.client.force_login(self.employee)
        response = self.post_leave(self.monday + timedelta(days=2), self.monday + timedelta(days=9))
        self.assertContains(response, 'masz już złożony')

    def test_rejects_insufficient_days(self):
        self.profile.annual_leave_days, self.profile.carried_over_days = 3, 0
        self.profile.save()
        self.client.force_login(self.employee)
        self.assertContains(self.post_leave(self.monday, self.monday + timedelta(days=4)), 'Niewystarczająca')

    def test_unpaid_leave_does_not_use_pool(self):
        self.profile.annual_leave_days, self.profile.carried_over_days = 0, 0
        self.profile.save()
        self.client.force_login(self.employee)
        self.post_leave(self.monday, self.monday + timedelta(days=4), kind='unpaid')
        self.assertEqual(LeaveRequest.objects.count(), 1)

    def test_on_demand_limit(self):
        self.client.force_login(self.employee)
        response = self.post_leave(self.monday, self.monday + timedelta(days=4), kind='on_demand')
        self.assertContains(response, 'Limit urlopu na żądanie')

    def test_cancel_pending(self):
        leave = self.leave()
        self.client.force_login(self.employee)
        self.client.post(reverse('hr:leave_cancel', args=[leave.pk]))
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveRequest.Status.CANCELLED)
        self.assertEqual(self.profile.leave_remaining, 22)

    def test_cannot_cancel_approved(self):
        leave = self.leave(status=LeaveRequest.Status.APPROVED)
        self.client.force_login(self.employee)
        self.assertEqual(self.client.post(reverse('hr:leave_cancel', args=[leave.pk])).status_code, 404)


class ReviewTests(HRBase):
    def test_review_list_shows_pending_by_default(self):
        self.leave()
        self.leave(start=self.monday + timedelta(weeks=3), status=LeaveRequest.Status.APPROVED)
        self.client.force_login(self.hr)
        response = self.client.get(reverse('hr:leave_review'))
        self.assertEqual(len(response.context['leave_requests']), 1)
        response = self.client.get(reverse('hr:leave_review'), {'status': ''})
        self.assertEqual(len(response.context['leave_requests']), 2)

    def test_approve(self):
        leave = self.leave()
        self.client.force_login(self.hr)
        response = self.client.post(leave.get_absolute_url(), {'decision': 'approved', 'comment': ''})
        self.assertRedirects(response, reverse('hr:leave_review'))
        leave.refresh_from_db()
        self.assertEqual(leave.status, LeaveRequest.Status.APPROVED)
        self.assertEqual(leave.reviewed_by, self.hr)
        self.assertEqual(mail.outbox[-1].to, ['jan@example.com'])

    def test_reject_requires_comment(self):
        leave = self.leave()
        self.client.force_login(self.hr)
        response = self.client.post(leave.get_absolute_url(), {'decision': 'rejected', 'comment': ''})
        self.assertContains(response, 'Podaj powód')
        leave.refresh_from_db()
        self.assertTrue(leave.is_pending)

    def test_employee_cannot_review_own(self):
        leave = self.leave()
        self.client.force_login(self.employee)
        response = self.client.post(leave.get_absolute_url(), {'decision': 'approved'})
        self.assertEqual(response.status_code, 403)

    def test_cannot_review_twice(self):
        leave = self.leave(status=LeaveRequest.Status.REJECTED)
        self.client.force_login(self.hr)
        self.assertEqual(self.client.post(leave.get_absolute_url(), {'decision': 'approved'}).status_code, 403)


class AnnouncementTests(HRBase):
    def test_hr_creates_and_employee_sees(self):
        self.client.force_login(self.hr)
        self.client.post(reverse('hr:announcement_create'), {'title': 'Szkolenie BHP', 'body': 'W piątek.',
                                                             'is_published': 'on'})
        self.client.force_login(self.employee)
        self.assertContains(self.client.get(reverse('hr:dashboard')), 'Szkolenie BHP')

    def test_unpublished_hidden_from_employee(self):
        a = Announcement.objects.create(title='Szkic', body='...', is_published=False)
        self.client.force_login(self.employee)
        self.assertNotContains(self.client.get(reverse('hr:announcements')), 'Szkic')
        self.assertEqual(self.client.get(a.get_absolute_url()).status_code, 404)
