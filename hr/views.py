from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (CreateView, DeleteView, DetailView, ListView, TemplateView,
                                  UpdateView)

from . import notifications
from .forms import AnnouncementForm, LeaveFilterForm, LeaveRequestForm, LeaveReviewForm
from .models import Announcement, LeaveRequest

REVIEW_PERM = 'hr.review_leaverequest'


class HRPortalMixin(LoginRequiredMixin):
    """Każdy widok portalu HR wymaga zalogowania."""
    hr_section = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['hr_section'] = self.hr_section
        if self.request.user.has_perm(REVIEW_PERM):
            ctx['hr_pending_count'] = LeaveRequest.objects.filter(status=LeaveRequest.Status.PENDING).count()
        return ctx


def visible_announcements(user):
    qs = Announcement.objects.select_related('created_by')
    if not user.has_perm('hr.change_announcement'):
        qs = qs.filter(is_published=True)
    return qs


# --- Pulpit ---------------------------------------------------------------

class DashboardView(HRPortalMixin, TemplateView):
    template_name = 'hr/dashboard.html'
    hr_section = 'dashboard'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx['profile'] = getattr(user, 'hr_profile', None)
        ctx['announcements'] = visible_announcements(user).filter(is_published=True)[:3]
        ctx['my_requests'] = user.leave_requests.all()[:5]
        today = timezone.localdate()
        ctx['upcoming_leave'] = user.leave_requests.filter(
            status=LeaveRequest.Status.APPROVED, end_date__gte=today).order_by('start_date').first()
        return ctx


# --- Ogłoszenia -------------------------------------------------------------

class AnnouncementListView(HRPortalMixin, ListView):
    template_name = 'hr/announcement_list.html'
    context_object_name = 'announcements'
    paginate_by = 10
    hr_section = 'announcements'

    def get_queryset(self):
        return visible_announcements(self.request.user)


class AnnouncementDetailView(HRPortalMixin, DetailView):
    template_name = 'hr/announcement_detail.html'
    context_object_name = 'announcement'
    hr_section = 'announcements'

    def get_queryset(self):
        return visible_announcements(self.request.user)


class AnnouncementFormMixin(HRPortalMixin, PermissionRequiredMixin):
    model = Announcement
    form_class = AnnouncementForm
    template_name = 'hr/announcement_form.html'
    hr_section = 'announcements'


class AnnouncementCreateView(AnnouncementFormMixin, CreateView):
    permission_required = 'hr.add_announcement'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Ogłoszenie zostało opublikowane.')
        return super().form_valid(form)


class AnnouncementUpdateView(AnnouncementFormMixin, UpdateView):
    permission_required = 'hr.change_announcement'

    def form_valid(self, form):
        messages.success(self.request, 'Zmiany zostały zapisane.')
        return super().form_valid(form)


class AnnouncementDeleteView(HRPortalMixin, PermissionRequiredMixin, DeleteView):
    model = Announcement
    permission_required = 'hr.delete_announcement'
    template_name = 'hr/confirm_delete.html'
    success_url = reverse_lazy('hr:announcements')
    hr_section = 'announcements'

    def form_valid(self, form):
        messages.success(self.request, 'Ogłoszenie zostało usunięte.')
        return super().form_valid(form)


# --- Moje dane --------------------------------------------------------------

class MyProfileView(HRPortalMixin, TemplateView):
    template_name = 'hr/my_profile.html'
    hr_section = 'profile'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        profile = getattr(self.request.user, 'hr_profile', None)
        ctx['profile'] = profile
        ctx['entry'] = profile.phonebook_entry if profile else None
        if profile:
            year = timezone.localdate().year
            ctx['year'] = year
            ctx['leave_approved'] = profile.leave_used(year, include_pending=False)
            ctx['leave_pending'] = profile.leave_used(year) - ctx['leave_approved']
            ctx['on_demand_used'] = sum(self.request.user.leave_requests.filter(
                leave_type=LeaveRequest.LeaveType.ON_DEMAND, start_date__year=year,
                status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
            ).values_list('days', flat=True))
            ctx['on_demand_limit'] = LeaveRequest.ON_DEMAND_LIMIT
        return ctx


# --- Wnioski urlopowe -------------------------------------------------------

class MyLeaveListView(HRPortalMixin, ListView):
    template_name = 'hr/leave_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 20
    hr_section = 'leave'

    def get_queryset(self):
        return self.request.user.leave_requests.select_related('reviewed_by')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile'] = getattr(self.request.user, 'hr_profile', None)
        return ctx


class LeaveCreateView(HRPortalMixin, CreateView):
    form_class = LeaveRequestForm
    template_name = 'hr/leave_form.html'
    hr_section = 'leave'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'user': self.request.user}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['profile'] = getattr(self.request.user, 'hr_profile', None)
        return ctx

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        notifications.leave_submitted(self.request, self.object)
        messages.success(self.request, f'Wniosek został złożony ({self.object.days} dni roboczych).')
        return response


class LeaveDetailView(HRPortalMixin, DetailView):
    template_name = 'hr/leave_detail.html'
    context_object_name = 'leave'
    hr_section = 'leave'

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related('user', 'reviewed_by', 'user__hr_profile')
        if self.request.user.has_perm(REVIEW_PERM):
            return qs
        return qs.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        leave = self.object
        can_review = self.request.user.has_perm(REVIEW_PERM) and leave.is_pending
        ctx['can_review'] = can_review
        ctx['can_cancel'] = leave.user == self.request.user and leave.is_pending
        if can_review:
            ctx['review_form'] = kwargs.get('review_form') or LeaveReviewForm()
            ctx['employee_profile'] = getattr(leave.user, 'hr_profile', None)
        if leave.user != self.request.user:
            self.hr_section = 'review'
            ctx['hr_section'] = 'review'
        return ctx

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not (request.user.has_perm(REVIEW_PERM) and self.object.is_pending):
            raise PermissionDenied
        form = LeaveReviewForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(review_form=form))
        leave = self.object
        leave.status = form.cleaned_data['decision']
        leave.review_comment = form.cleaned_data['comment']
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.save()
        notifications.leave_reviewed(request, leave)
        messages.success(request, f'Wniosek: {leave.get_status_display().lower()}.')
        return redirect('hr:leave_review')


class LeaveCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk, user=request.user, status=LeaveRequest.Status.PENDING)
        leave.status = LeaveRequest.Status.CANCELLED
        leave.save()
        messages.success(request, 'Wniosek został anulowany.')
        return redirect('hr:leave_list')


class LeaveReviewListView(HRPortalMixin, PermissionRequiredMixin, ListView):
    permission_required = REVIEW_PERM
    template_name = 'hr/leave_review_list.html'
    context_object_name = 'leave_requests'
    paginate_by = 30
    hr_section = 'review'

    def get_queryset(self):
        qs = LeaveRequest.objects.select_related('user', 'reviewed_by')
        data = self.request.GET.copy()
        if 'status' not in data:
            data['status'] = LeaveRequest.Status.PENDING
        self.filter_form = LeaveFilterForm(data)
        if self.filter_form.is_valid():
            status, q = self.filter_form.cleaned_data['status'], self.filter_form.cleaned_data['q']
            if status:
                qs = qs.filter(status=status)
            for word in q.split():
                qs = qs.filter(Q(user__first_name__icontains=word) | Q(user__last_name__icontains=word)
                               | Q(user__username__icontains=word))
        if self.filter_form.cleaned_data.get('status') == LeaveRequest.Status.PENDING:
            qs = qs.order_by('start_date')
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = self.filter_form
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['querystring'] = params.urlencode()
        return ctx
