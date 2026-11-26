from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse_lazy
from django.db.models import Prefetch
from django.views.generic import FormView, TemplateView

from .forms import ContactForm
from .models import LinkGroup, UsefulLink


class HomeView(TemplateView):
    template_name = 'pages/home.html'


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('pages:contact')

    def form_valid(self, form):
        data = form.cleaned_data
        send_mail(
            subject=f"[Kontakt] {data['subject']}",
            message=f"Od: {data['name']} <{data['email']}>\n\n{data['message']}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.CONTACT_EMAIL],
        )
        messages.success(self.request, 'Dziękujemy! Wiadomość została wysłana.')
        return super().form_valid(form)


class UsefulLinksView(TemplateView):
    template_name = 'pages/links.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        active = UsefulLink.objects.filter(is_active=True)
        ctx['groups'] = [g for g in LinkGroup.objects.prefetch_related(
            Prefetch('links', queryset=active, to_attr='active_links')) if g.active_links]
        ctx['ungrouped'] = active.filter(group__isnull=True)
        return ctx
