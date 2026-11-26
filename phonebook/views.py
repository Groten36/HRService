from django.views.generic import ListView

from hrservice.mixins import OptionalLoginRequiredMixin

from .forms import EmployeeSearchForm
from .models import Employee


class EmployeeListView(OptionalLoginRequiredMixin, ListView):
    login_setting = 'PHONEBOOK_REQUIRE_LOGIN'
    template_name = 'phonebook/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 50

    def get_template_names(self):
        # Zapytania z wyszukiwarki na żywo dostają tylko fragment z wynikami
        if self.request.headers.get('X-Requested-With') == 'fetch':
            return ['phonebook/_results.html']
        return [self.template_name]

    def get_queryset(self):
        qs = Employee.objects.select_related('department', 'section')
        self.form = EmployeeSearchForm(self.request.GET or None)
        if self.form.is_valid():
            data = self.form.cleaned_data
            for word in data['q'].lower().split():
                qs = qs.filter(search_text__contains=word)
            if data['department']:
                qs = qs.filter(department=data['department'])
            if data['section']:
                qs = qs.filter(section=data['section'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['form'] = self.form
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['querystring'] = params.urlencode()
        ctx['is_filtered'] = any(self.request.GET.get(k) for k in ('q', 'department', 'section'))
        return ctx
