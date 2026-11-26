from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, FormView, ListView, TemplateView, UpdateView

from .forms import AdminSetPasswordForm, UserCreateForm, UserFilterForm, UserUpdateForm
from .roles import ROLES, ROLES_BY_KEY, get_role, set_role


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'registration/profile.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['role'] = get_role(self.request.user)
        return ctx


# --- Zarządzanie użytkownikami (Administrator IT) ---------------------------

class ProtectSuperusersMixin:
    """Tylko superuser może edytować/usuwać innych superuserów."""

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.is_superuser and not self.request.user.is_superuser:
            raise PermissionDenied('Nie możesz modyfikować konta superużytkownika.')
        return obj


class UserListView(PermissionRequiredMixin, ListView):
    permission_required = 'auth.view_user'
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 30

    def get_queryset(self):
        qs = User.objects.prefetch_related('groups').order_by('last_name', 'first_name', 'username')
        self.filter_form = UserFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            for word in self.filter_form.cleaned_data['q'].split():
                qs = qs.filter(Q(username__icontains=word) | Q(first_name__icontains=word)
                               | Q(last_name__icontains=word) | Q(email__icontains=word))
            role = self.filter_form.cleaned_data['role']
            if role:
                qs = qs.filter(groups__name=ROLES_BY_KEY[role].name)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        for u in ctx['users']:
            u.role = get_role(u)
        ctx['filter_form'] = self.filter_form
        ctx['roles'] = ROLES
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['querystring'] = params.urlencode()
        return ctx


class UserCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'auth.add_user'
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        set_role(self.object, form.cleaned_data['role'])
        messages.success(self.request, f'Utworzono konto „{self.object.username}”.')
        return response


class UserUpdateView(PermissionRequiredMixin, ProtectSuperusersMixin, UpdateView):
    permission_required = 'auth.change_user'
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_list')
    context_object_name = 'edited_user'

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'editor': self.request.user}

    def form_valid(self, form):
        response = super().form_valid(form)
        if 'role' in form.changed_data and not form.fields['role'].disabled:
            set_role(self.object, form.cleaned_data['role'])
        messages.success(self.request, 'Zmiany zostały zapisane.')
        return response


class UserSetPasswordView(PermissionRequiredMixin, FormView):
    permission_required = 'auth.change_user'
    form_class = AdminSetPasswordForm
    template_name = 'accounts/user_password.html'
    success_url = reverse_lazy('user_list')

    def dispatch(self, request, *args, **kwargs):
        self.edited_user = get_object_or_404(User, pk=kwargs['pk'])
        if self.edited_user.is_superuser and not request.user.is_superuser:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), 'user': self.edited_user}

    def get_context_data(self, **kwargs):
        return {**super().get_context_data(**kwargs), 'edited_user': self.edited_user}

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Ustawiono nowe hasło dla „{self.edited_user.username}”.')
        return super().form_valid(form)


class UserDeleteView(PermissionRequiredMixin, ProtectSuperusersMixin, DeleteView):
    permission_required = 'auth.delete_user'
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')
    context_object_name = 'edited_user'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj == self.request.user:
            raise PermissionDenied('Nie możesz usunąć własnego konta.')
        return obj

    def form_valid(self, form):
        messages.success(self.request, f'Usunięto konto „{self.object.username}”.')
        return super().form_valid(form)
