from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from hrservice.mixins import OptionalLoginRequiredMixin

from .forms import DocumentFilterForm, DocumentForm
from .models import Category, Document


class VisibleDocumentsMixin(OptionalLoginRequiredMixin):
    """Pracownicy widzą opublikowane dokumenty; osoby z prawem edycji — wszystkie.

    Logowanie jest wymagane tylko gdy settings.DOCUMENTS_REQUIRE_LOGIN = True.
    """

    login_setting = 'DOCUMENTS_REQUIRE_LOGIN'

    def get_queryset(self):
        qs = Document.objects.select_related('category', 'uploaded_by')
        if not self.request.user.has_perm('documents.change_document'):
            qs = qs.filter(is_published=True)
        return qs


class DocumentListView(VisibleDocumentsMixin, ListView):
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'
    paginate_by = 15
    kind = None  # ustawiane w urls.py, np. dla strony „Programy”

    def get_queryset(self):
        qs = super().get_queryset()
        if self.kind:
            qs = qs.filter(kind=self.kind)
        self.current_category = None
        if 'slug' in self.kwargs:
            self.current_category = get_object_or_404(Category, slug=self.kwargs['slug'])
            qs = qs.filter(category=self.current_category)
        self.filter_form = DocumentFilterForm(self.request.GET or None)
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            if data['q']:
                qs = qs.filter(
                    Q(title__icontains=data['q'])
                    | Q(number__icontains=data['q'])
                    | Q(description__icontains=data['q'])
                )
            if data['kind'] and not self.kind:
                qs = qs.filter(kind=data['kind'])
            if data['category'] and not self.current_category:
                qs = qs.filter(category=data['category'])
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = self.filter_form
        ctx['current_category'] = self.current_category
        ctx['current_kind'] = self.kind
        params = self.request.GET.copy()
        params.pop('page', None)
        ctx['querystring'] = params.urlencode()
        return ctx


class DocumentDetailView(VisibleDocumentsMixin, DetailView):
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'


class DocumentDownloadView(VisibleDocumentsMixin, View):
    def get(self, request, pk):
        document = get_object_or_404(self.get_queryset(), pk=pk)
        try:
            handle = document.file.open('rb')
        except FileNotFoundError:
            raise Http404('Plik nie istnieje.')
        inline = request.GET.get('inline') == '1' and document.extension == 'PDF'
        return FileResponse(handle, as_attachment=not inline,
                            filename=document.original_filename)


class DocumentFormMixin:
    model = Document
    form_class = DocumentForm
    template_name = 'documents/document_form.html'

    def form_valid(self, form):
        if 'file' in form.changed_data:
            form.instance.original_filename = form.cleaned_data['file'].name
        return super().form_valid(form)


class DocumentCreateView(PermissionRequiredMixin, DocumentFormMixin, CreateView):
    permission_required = 'documents.add_document'

    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('kind') in Document.Kind.values:
            initial['kind'] = self.request.GET['kind']
        return initial

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        messages.success(self.request, 'Dokument został dodany.')
        return super().form_valid(form)


class DocumentUpdateView(PermissionRequiredMixin, DocumentFormMixin, UpdateView):
    permission_required = 'documents.change_document'

    def form_valid(self, form):
        messages.success(self.request, 'Zmiany zostały zapisane.')
        return super().form_valid(form)


class DocumentDeleteView(PermissionRequiredMixin, DeleteView):
    model = Document
    permission_required = 'documents.delete_document'
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('documents:list')

    def form_valid(self, form):
        messages.success(self.request, f'Usunięto dokument „{self.object}”.')
        return super().form_valid(form)
